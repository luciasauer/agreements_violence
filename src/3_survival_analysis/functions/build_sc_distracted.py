import pandas as pd
import numpy as np


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

    members_sc.loc[members_sc['country'].isna() & members_sc['year'].isin([1990, 1991, 2018, 2019]), 'country'] = "Côte d'Ivoire"
    members_sc.loc[members_sc['country'].isna() & members_sc['year'].isin([2009, 2010]), 'country'] = 'Turkey'

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
        print('WARNING: unmapped SC members:\n', null_members[['year', 'country']].drop_duplicates().to_string())

    return members_sc


def build_sc_distracted(
    esd_path: str,
    members_sc_path: str,
    isocodes_path: str,
) -> pd.DataFrame:
    """
    Build SC-distraction instrument at country × year level.

    For each conflict-location country i in year y:

        sc_at_war_outside_isocode  = (total_SC_involvement - SC_involvement_in_i)
                                     / total_SC_involvement

    High value (~1) → SC members are busy in other countries → distracted from i.
    Low value (~0)  → SC involvement concentrated in i.

    Countries not in the ESD (no SC member supporting conflicts there) get NaN;
    the caller should fillna(1) — meaning all SC activity is elsewhere.

    Parameters
    ----------
    esd_path        : path to ucdp-esd-ty-181.xlsx
    members_sc_path : path to DPPA-SCMEMBERSHIP.csv
    isocodes_path   : path to isocodes_appended.csv

    Returns
    -------
    DataFrame with columns:
        isocode, year,
        sc_at_war_outside_isocode,
        sc_at_war_outside_sub_region,
        sc_at_war_outside_region
    """
    isocodes   = _load_isocodes(isocodes_path)
    members_sc = _load_members_sc(members_sc_path, isocodes)

    # ── Load and filter ESD ───────────────────────────────────────────────────
    esd = pd.read_excel(
        esd_path,
        usecols=['id', 'year', 'ext_name', 'ext_sup', 'ext_nonstate', 'active', 'country_a']
    )
    esd = esd.loc[
        (esd['active'] == 1) &
        (esd['year'] >= 1989) &
        (esd['ext_sup'] == 1) &
        (esd['ext_nonstate'] == 0)
    ].copy()

    esd['ext_name']  = esd['ext_name'].str.replace('Government of ', '', regex=False).str.strip()
    esd['country_a'] = esd['country_a'].str.strip()

    # ── Map supporter name → isocode ─────────────────────────────────────────
    esd = esd.merge(
        isocodes[['name', 'alpha_3']], left_on='ext_name', right_on='name', how='left'
    ).rename(columns={'alpha_3': 'isocode_supporter'}).drop(columns=['name'])

    _manual = {
        'Vietnam (North Vietnam)': 'VNM',
        'Nepalese elements':       'NPL',
        'East Germany':            'DEU',
        'Sudanese elements':       'SDN',
        'South African elements':  'ZAF',
        'Bangladeshi elements':    'BGD',
        'Indian elements':         'IND',
        'Bhutanese elements':      'BTN',
        'Russian elements':        'RUS',
        'Malaysian elements':      'MYS',
        'Congolese elements':      'COG',
    }
    esd['isocode_supporter'] = esd.apply(
        lambda r: _manual.get(r['ext_name'], r['isocode_supporter'])
        if pd.isna(r['isocode_supporter']) else r['isocode_supporter'],
        axis=1,
    )
    esd = esd.dropna(subset=['isocode_supporter']).reset_index(drop=True)

    # ── Map war location → isocode + region ──────────────────────────────────
    esd = esd.merge(
        isocodes[['name', 'alpha_3', 'region', 'sub_region']],
        left_on='country_a', right_on='name', how='left'
    ).rename(columns={'alpha_3': 'isocode_war_location'}).drop(columns=['name'])

    # ── Keep only SC-member supporters ───────────────────────────────────────
    sc = (
        members_sc[['year', 'isocode']]
        .rename(columns={'isocode': 'isocode_supporter'})
        .drop_duplicates()
    )
    esd_sc = esd.merge(sc, on=['year', 'isocode_supporter'], how='inner')

    # ── Count distinct SC members involved per location-year ─────────────────
    invol = (
        esd_sc
        .groupby(['year', 'isocode_supporter', 'isocode_war_location', 'region', 'sub_region'],
                 as_index=False)
        .agg(n_events=('id', 'nunique'))
    )

    loc_year = (
        invol
        .groupby(['year', 'isocode_war_location', 'sub_region', 'region'], as_index=False)
        .agg(sc_in_country=('isocode_supporter', 'nunique'))
    )

    # ── Compute "outside" fractions ───────────────────────────────────────────
    loc_year['total']      = loc_year.groupby('year')['sc_in_country'].transform('sum')
    loc_year['in_region']  = loc_year.groupby(['year', 'region'])['sc_in_country'].transform('sum')
    loc_year['in_subreg']  = loc_year.groupby(['year', 'sub_region'])['sc_in_country'].transform('sum')

    loc_year['sc_at_war_outside_isocode']    = (loc_year['total'] - loc_year['sc_in_country']) / loc_year['total']
    loc_year['sc_at_war_outside_region']     = (loc_year['total'] - loc_year['in_region'])     / loc_year['total']
    loc_year['sc_at_war_outside_sub_region'] = (loc_year['total'] - loc_year['in_subreg'])     / loc_year['total']

    return (
        loc_year
        .rename(columns={'isocode_war_location': 'isocode'})
        [['isocode', 'year',
          'sc_at_war_outside_isocode',
          'sc_at_war_outside_sub_region',
          'sc_at_war_outside_region']]
    )


def build_rebel_ext_support(esd_path: str) -> pd.DataFrame:
    """
    Build rebel external support indicator at conflict_id × year level.

    rebel_ext_support = 1 if any non-state actor in that conflict-year
    received foreign military support (UCDP ESD).

    Coverage: 1975–2017. Years outside this range should be imputed as 0
    after merging.

    Parameters
    ----------
    esd_path : path to ucdp-esd-ty-181.xlsx

    Returns
    -------
    DataFrame with columns: conflict_id, year, rebel_ext_support (=1)
    """
    esd = pd.read_excel(
        esd_path,
        usecols=['conflict_id', 'year', 'actor_nonstate', 'ext_sum']
    )
    rebel = (
        esd[(esd['actor_nonstate'] == 1) & (esd['ext_sum'] > 0)]
        .groupby(['conflict_id', 'year'])
        .size()
        .reset_index(name='_n')
        .assign(rebel_ext_support=1)[['conflict_id', 'year', 'rebel_ext_support']]
        .drop_duplicates()
    )
    return rebel
