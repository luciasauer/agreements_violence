import pandas as pd
import numpy as np
import warnings
from itertools import combinations
from pandas.errors import PerformanceWarning

warnings.filterwarnings("ignore", category=PerformanceWarning)
pd.set_option('future.no_silent_downcasting', True)


def _load_isocodes(isocodes_path: str) -> pd.DataFrame:
    isocodes = pd.read_csv(isocodes_path, sep=';')
    isocodes[['region', 'sub_region']] = (
        isocodes
        .groupby('alpha_3')[['region', 'sub_region']]
        .transform(lambda s: s.ffill().bfill())
    )
    return isocodes.drop_duplicates(subset=['alpha_3'], keep='first').reset_index(drop=True)


def _load_members_sc(members_sc_path: str, isocodes: pd.DataFrame) -> pd.DataFrame:
    members_sc = (
        pd.read_csv(members_sc_path, usecols=['year', 'security_council_member'])
        .rename(columns={'security_council_member': 'country'})
    )
    members_sc = members_sc[members_sc['year'] >= 1989].copy()

    _civ_years = [1990, 1991, 2018, 2019]
    members_sc.loc[members_sc['country'].isna() & members_sc['year'].isin(_civ_years), 'country'] = "Côte d'Ivoire"
    members_sc.loc[
        members_sc['country'].isna() & members_sc['year'].isin([2009, 2010]), 'country'
    ] = 'Turkey'

    name_fix = {
        'USSR (Union of Soviet Socialist Republics)': 'Russian Federation',
        "Ivory Coast":                                "Côte d'Ivoire",
        'Republic of Korea':                          'Korea, Republic of',
        'United Republic of Tanzania':                'Tanzania, United Republic of',
        'Democratic Republic of the Congo':           'Congo, Democratic Republic of the',
    }
    members_sc['country'] = members_sc['country'].replace(name_fix)

    members_sc = (
        members_sc
        .merge(isocodes[['name', 'alpha_3']], left_on='country', right_on='name', how='left')
        .rename(columns={'alpha_3': 'isocode'})
        .drop(columns=['name'])
    )

    null_members = members_sc[members_sc['isocode'].isna()]
    if len(null_members):
        unmapped = null_members[['year', 'country']].drop_duplicates().to_string()
        print(f'WARNING: unmapped SC members:\n{unmapped}')

    return members_sc


def _load_votes(votes_path: str, isocodes: pd.DataFrame) -> pd.DataFrame:
    votes = pd.read_csv(
        votes_path, low_memory=False,
        usecols=['ms_code', 'ms_name', 'ms_vote', 'date', 'resolution']
    )
    votes['date'] = pd.to_datetime(votes['date'])
    votes = votes.loc[votes['date'].dt.year >= 1968].copy()
    votes['year'] = votes['date'].dt.year

    votes = votes.loc[votes['ms_vote'].isin(['Y', 'N', 'A'])].copy()
    votes = votes.rename(columns={'ms_vote': 'vote'})
    votes['vote'] = votes['vote'].map({'Y': 1, 'N': 0, 'A': 2})

    code_fix = {'GER': 'DEU', 'CSK': 'CZE', 'SUN': 'RUS'}
    votes['ms_code'] = votes['ms_code'].replace(code_fix)

    votes = (
        votes
        .merge(isocodes[['alpha_3', 'name']], left_on='ms_code', right_on='alpha_3', how='left')
        .rename(columns={'name': 'country', 'alpha_3': 'isocode'})
    )
    return votes[['isocode', 'vote', 'year', 'resolution']]


def _load_gdp(gdp_path: str) -> pd.DataFrame:
    gdp = (
        pd.read_csv(gdp_path, low_memory=False)
        .rename(columns={'gdp_current_usd': 'gdp'})
    )
    gdp['year_mo'] = pd.to_datetime(gdp['year_mo'])
    gdp = gdp.loc[gdp['year_mo'].dt.month == 6].copy()
    gdp['year'] = gdp['year_mo'].dt.year
    gdp = gdp.loc[gdp['year'] >= 1989, ['isocode', 'year', 'gdp']].copy()

    missing_by_iso = (
        gdp.assign(missing_gdp=lambda x: x['gdp'].isna())
        .groupby('isocode', as_index=False)['missing_gdp'].sum()
    )
    valid_isos = set(missing_by_iso.loc[missing_by_iso['missing_gdp'] < 20, 'isocode'])
    gdp = gdp[gdp['isocode'].isin(valid_isos)].copy()

    gdp = gdp.sort_values(['isocode', 'year'])
    gdp['gdp'] = gdp.groupby('isocode')['gdp'].ffill().bfill()

    gdp['log_gdp'] = np.log1p(gdp['gdp'])
    gdp['max_gdp'] = gdp.groupby('year')['gdp'].transform('max')
    gdp['max_log_gdp'] = gdp.groupby('year')['log_gdp'].transform('max')
    gdp['gdp_normalized'] = gdp['gdp'] / gdp['max_gdp']
    gdp['log_gdp_normalized'] = gdp['log_gdp'] / gdp['max_log_gdp']

    return gdp.drop(columns=['max_gdp', 'max_log_gdp'])


def _compute_similarity(votes_window: pd.DataFrame) -> pd.DataFrame:
    """
    Compute average fraction of resolutions where each country-pair voted the same,
    over the supplied window. Returns symmetric pairs DataFrame.
    """
    pairs = []
    for _, g in votes_window.groupby('resolution'):
        d = dict(zip(g['isocode'], g['vote'], strict=False))
        for c1, c2 in combinations(d.keys(), 2):
            pairs.append({'isocode1': c1, 'isocode2': c2, 'same_vote': int(d[c1] == d[c2])})

    if not pairs:
        return pd.DataFrame(columns=['isocode1', 'isocode2', 'same_vote'])

    pairs_df = pd.DataFrame(pairs)
    similarity = (
        pairs_df
        .groupby(['isocode1', 'isocode2'], as_index=False)['same_vote']
        .mean()
    )

    # Symmetrise so every country appears in isocode1.
    # combinations() stores each pair in one order only; without this, SC members
    # that ended up in isocode2 are silently dropped when filtering by isocode2.
    mirror = similarity.rename(columns={'isocode1': 'isocode2', 'isocode2': 'isocode1'})
    return (
        pd.concat([similarity, mirror], ignore_index=True)
        .groupby(['isocode1', 'isocode2'], as_index=False)['same_vote']
        .mean()
    )


def build_influence_scores(
    votes_path: str,
    members_sc_path: str,
    isocodes_path: str,
    gdp_path: str | None = None,
    year_range: tuple[int, int] = (1989, 2023),
    sim_lag_lo: int = 20,
    sim_lag_hi: int = 5,
) -> pd.DataFrame:
    """
    Build UN SC voting-alignment influence scores at country × year level.

    For each recipient country i in year y:

        influence_veto_{i,y} = sum_{j in SC(y)} same_vote_{i,j,[y-lag_hi, y-lag_lo]} * veto_factor_j

    where veto_factor_j = 10 for P5 members, 1 otherwise.
    Voting similarity is computed over the window [y - sim_lag_lo, y - sim_lag_hi].

    Parameters
    ----------
    votes_path      : path to 2025_9_19_ga_voting.csv
    members_sc_path : path to DPPA-SCMEMBERSHIP.csv
    isocodes_path   : path to isocodes_appended.csv
    gdp_path        : (optional) path to gdp_pc.csv — if provided, also returns
                      influence_gdp and influence_log_gdp columns
    year_range      : (first_year, last_year) inclusive
    sim_lag_lo      : lower lag for voting window (default 20 years)
    sim_lag_hi      : upper lag for voting window (default 5 years)

    Returns
    -------
    DataFrame with columns:
        isocode, year, influence, influence_veto
        [+ influence_gdp, influence_log_gdp  if gdp_path is provided]
    """
    isocodes   = _load_isocodes(isocodes_path)
    members_sc = _load_members_sc(members_sc_path, isocodes)
    votes      = _load_votes(votes_path, isocodes)
    gdp        = _load_gdp(gdp_path) if gdp_path else None

    p5 = {'USA', 'RUS', 'FRA', 'CHN', 'GBR'}

    # ── Step 1: similarity matrices per year ──────────────────────────────────
    sim_by_year = {}
    y_start, y_end = year_range
    for y in range(y_start, y_end + 1):
        lo, hi = y - sim_lag_lo, y - sim_lag_hi
        votes_window = votes.loc[
            (votes['year'] >= lo) & (votes['year'] <= hi),
            ['resolution', 'isocode', 'vote']
        ]
        sim_by_year[y] = (
            _compute_similarity(votes_window)
            if not votes_window.empty
            else pd.DataFrame(columns=['isocode1', 'isocode2', 'same_vote'])
        )

    # ── Step 2: weight by SC membership and veto factor ───────────────────────
    influence_scores_list = []

    for y in range(y_start, y_end + 1):
        sim_y = sim_by_year.get(y)
        if sim_y is None or sim_y.empty:
            continue

        members_y = (
            members_sc.loc[members_sc['year'] == y, 'isocode']
            .dropna().unique()
        )
        if len(members_y) == 0:
            continue

        sim_y = sim_y[sim_y['isocode2'].isin(members_y)].copy()
        if sim_y.empty:
            continue

        sim_y['veto_factor'] = np.where(sim_y['isocode2'].isin(p5), 10.0, 1.0)
        sim_y['inf_raw']  = sim_y['same_vote']
        sim_y['inf_veto'] = sim_y['same_vote'] * sim_y['veto_factor']

        agg_dict = {'influence': ('inf_raw', 'sum'), 'influence_veto': ('inf_veto', 'sum')}

        if gdp is not None:
            gdp_y = (
                gdp.loc[gdp['year'] == y, ['isocode', 'gdp_normalized', 'log_gdp_normalized']]
                .rename(columns={'isocode': 'isocode2'})
            )
            sim_y = sim_y.merge(gdp_y, on='isocode2', how='left')
            sim_y['inf_gdp']     = sim_y['same_vote'] * sim_y['gdp_normalized'].fillna(0.0)
            sim_y['inf_log_gdp'] = sim_y['same_vote'] * sim_y['log_gdp_normalized'].fillna(0.0)
            agg_dict['influence_gdp']     = ('inf_gdp',     'sum')
            agg_dict['influence_log_gdp'] = ('inf_log_gdp', 'sum')

        infl_y = (
            sim_y.groupby('isocode1', as_index=False)
            .agg(**agg_dict)
            .rename(columns={'isocode1': 'isocode'})
        )
        infl_y['year'] = y
        influence_scores_list.append(infl_y)

    return pd.concat(influence_scores_list, ignore_index=True)
