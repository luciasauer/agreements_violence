"""
build_onset_covariates.py
=========================
Onset-level covariates for the survival analysis spell dataset.

Functions
---------
build_pko_onset(df_panel, pko_path)
    Adds pko_onset and pko_ever from Geo-PKO v2.3.

build_defpact_onset(df_panel, qog_path, atop_dy_path)
    Adds defpact_onset and defpact_majpow_onset from ATOP.

build_loot_onset(df_panel, ged_path, prio_static_path, prio_yearly_path)
    Adds loot_onset_strict and loot_onset from PRIO-GRID.

build_distance_onset(df_panel, ged_path, prio_yearly_path)
    Adds bdist_onset and capdist_onset from PRIO-GRID.

build_mountains_onset(df_panel, ged_path, prio_static_path)
    Adds mountains_onset from PRIO-GRID static mountains_mean.

Output columns
--------------
pko_onset
    1 if a UN peacekeeping operation was deployed in the conflict country
    in the exact onset month. Source: Geo-PKO v2.3 (1994–2024).
    0 for the 98 conflicts with onset before 1994 (data starts 1994, not
    absence of PKO).

pko_ever
    1 if a PKO was deployed in the country at any point during the conflict
    spell (start_date to end_date). Endogenous to conflict intensity — use
    as a correlate, not a causal proxy.

defpact_onset
    1 if the country had any active defensive alliance in the onset year.
    Source: ATOP State-Year via QoG Standard Dataset (unbalanced panel;
    absent country-years → 0). Last updated Aug 2022; NaN only for the
    4 conflicts with onset after 2022.

defpact_majpow_onset
    1 if at least one defensive alliance partner was a major power
    (USA=2, UK=200, France=220, USSR/Russia=365, China=710).
    Source: ATOP v5.1 Dyad-Year file. Same NaN rule as defpact_onset.

loot_onset_strict
    =1 if any yearly PRIO-GRID resource layer (petroleum_y, diamsec_y,
    diamprim_y, gem_y, drug_y, goldplacer_y, goldvein_y, goldsurface_y)
    equals 1 for any onset cell at the conflict's onset year. Geographic
    footprint: GED events in first 90 days from start_date. No undated
    deposits — no risk of future contamination. Yearly data capped at 2014;
    post-2014 conflicts use 2014 values (forward-fill assumption).

loot_onset
    =1 if loot_onset_strict=1 OR any static layer (petroleum_s, diamsec_s,
    diamprim_s, gem_s, goldplacer_s, goldvein_s) equals 1 for any onset
    cell. Includes undated deposits (unknown discovery year — minor
    future-contamination risk). Source: PRIO-GRID 2.0 Static + Yearly.

bdist_onset
    Mean distance (km) to nearest national border across the onset-quarter
    GED cells. Low values indicate conflict near a border (cross-border
    sanctuary risk). Source: PRIO-GRID `bdist3`, yearly 1989–2014.

capdist_onset
    Mean distance (km) to country capital across the onset-quarter GED
    cells. High values indicate conflict far from capital (weak state
    administrative reach). Source: PRIO-GRID `capdist`, yearly 1989–2014.

mountains_onset
    Mean of PRIO-GRID `mountains_mean` (share of cell that is mountainous,
    Weidmann 2009) across the onset-quarter GED cells. High values indicate
    rough terrain — associated with rebel sanctuary and conflict persistence.
    Source: PRIO-GRID 2.0 Static Variables (time-invariant).
"""

import pandas as pd
import numpy as np

# COW numeric codes for major powers (Leeds et al. 2002)
_MAJOR_POWERS_COW = {2, 200, 220, 365, 710}

# ATOP was last updated August 2022. No new alliances appear for 2019–2022,
# so absent country-years through 2022 are reliably coded 0 (no alliance).
# Only onset > 2022 → NaN (unknown).
_ATOP_COVERAGE_END = 2022


# ── PKO ──────────────────────────────────────────────────────────────────────

def build_pko_onset(df_panel, pko_path):
    """
    Add pko_onset and pko_ever to df_panel.

    Parameters
    ----------
    df_panel : pd.DataFrame
        Conflict panel with columns: conflict_id, country, year_mo,
        start_date, end_date.
    pko_path : str
        Path to Geo-PKO v2.3 location-month CSV.

    Returns
    -------
    pd.DataFrame
        df_panel with pko_onset and pko_ever columns added.
    """
    pko_raw = pd.read_csv(pko_path, low_memory=False)

    _NAME_FIX = {
        'Bosnia and Herzegovina': 'Bosnia-Herzegovina',
        'DRC':                    'DR Congo (Zaire)',
    }
    pko_raw['country'] = pko_raw['country'].replace(_NAME_FIX)
    pko_raw['year_mo'] = (
        pko_raw['year'].astype(str) + '-' +
        pko_raw['month'].astype(str).str.zfill(2)
    )

    # Country × month presence indicator
    pko_monthly = (
        pko_raw
        .groupby(['country', 'year_mo'])
        .size()
        .reset_index(name='_n')
        .assign(pko_month=1)
        [['country', 'year_mo', 'pko_month']]
    )

    cl_onset = (
        df_panel
        .drop_duplicates('conflict_id')
        [['conflict_id', 'country', 'start_date']]
        .copy()
    )

    # pko_onset: PKO present in the onset month
    pko_onset_df = (
        cl_onset
        .merge(pko_monthly, left_on=['country', 'start_date'],
               right_on=['country', 'year_mo'], how='left')
        [['conflict_id', 'pko_month']]
        .fillna({'pko_month': 0})
        .rename(columns={'pko_month': 'pko_onset'})
        .assign(pko_onset=lambda d: d['pko_onset'].astype(int))
    )

    # pko_ever: PKO present at any month during the spell
    df_with_pko = df_panel.merge(pko_monthly, on=['country', 'year_mo'], how='left')
    df_with_pko['pko_month'] = df_with_pko['pko_month'].fillna(0).astype(int)
    spell_mask = (
        (df_with_pko['year_mo'] >= df_with_pko['start_date']) &
        (df_with_pko['year_mo'] <= df_with_pko['end_date'])
    )
    pko_ever_df = (
        df_with_pko[spell_mask]
        .groupby('conflict_id')['pko_month']
        .max()
        .reset_index()
        .rename(columns={'pko_month': 'pko_ever'})
        .assign(pko_ever=lambda d: d['pko_ever'].astype(int))
    )

    df_panel = df_panel.drop(columns=['pko_onset', 'pko_ever'], errors='ignore')
    df_panel = df_panel.merge(pko_onset_df, on='conflict_id', how='left')
    df_panel = df_panel.merge(pko_ever_df,  on='conflict_id', how='left')

    cl = df_panel.drop_duplicates('conflict_id')
    n_pre94 = (cl['start_date'].str[:4].astype(int) < 1994).sum()
    print(f"pko_onset = 1: {(cl['pko_onset']==1).sum()}  0: {(cl['pko_onset']==0).sum()}  "
          f"(of which pre-1994 onset: {n_pre94})")
    print(f"pko_ever  = 1: {(cl['pko_ever']==1).sum()}  0: {(cl['pko_ever']==0).sum()}")

    return df_panel


# ── DEFPACT ──────────────────────────────────────────────────────────────────

def build_defpact_onset(df_panel, qog_path, atop_dy_path):
    """
    Add defpact_onset and defpact_majpow_onset to df_panel.

    Parameters
    ----------
    df_panel : pd.DataFrame
        Conflict panel with columns: conflict_id, isocode, start_date.
    qog_path : str
        Path to QoG ATOP state-year CSV (sep=';', decimal=',').
        Used for defpact_onset and as COW→ISO crosswalk.
    atop_dy_path : str
        Path to ATOP v5.1 dyad-year CSV (atop5_1dy.csv).
        Used for defpact_majpow_onset.

    Returns
    -------
    pd.DataFrame
        df_panel with defpact_onset and defpact_majpow_onset columns added.
    """
    qog = pd.read_csv(qog_path, sep=';', decimal=',')
    cow_iso = qog[['ccodecow', 'ccodealp']].dropna().drop_duplicates()

    cl = (
        df_panel
        .drop_duplicates('conflict_id')
        [['conflict_id', 'isocode', 'start_date']]
        .copy()
    )
    cl['yr'] = cl['start_date'].str[:4].astype(int)

    # ── defpact_onset ─────────────────────────────────────────────────────────
    d1 = (
        cl.merge(qog[['ccodealp', 'year', 'atop_defensive']],
                 left_on=['isocode', 'yr'], right_on=['ccodealp', 'year'],
                 how='left')
        [['conflict_id', 'yr', 'atop_defensive']]
    )
    within = d1['yr'] <= _ATOP_COVERAGE_END
    d1.loc[within, 'atop_defensive'] = d1.loc[within, 'atop_defensive'].fillna(0)

    # ── defpact_majpow_onset ──────────────────────────────────────────────────
    dy = pd.read_csv(atop_dy_path)
    mp = dy[
        (dy['defense'] == 1) &
        (dy['mem1'].isin(_MAJOR_POWERS_COW) | dy['mem2'].isin(_MAJOR_POWERS_COW))
    ].copy()
    mp['partner_cow'] = mp.apply(
        lambda r: r['mem2'] if r['mem1'] in _MAJOR_POWERS_COW else r['mem1'], axis=1
    )
    mpsy = (
        mp.groupby(['partner_cow', 'year']).size().reset_index(name='_n')
        .assign(defpact_majpow=1)
        .merge(cow_iso, left_on='partner_cow', right_on='ccodecow', how='left')
    )
    d2 = (
        cl.merge(mpsy[['ccodealp', 'year', 'defpact_majpow']].dropna(subset=['ccodealp']),
                 left_on=['isocode', 'yr'], right_on=['ccodealp', 'year'],
                 how='left')
        [['conflict_id', 'yr', 'defpact_majpow']]
    )
    within2 = d2['yr'] <= _ATOP_COVERAGE_END
    d2.loc[within2, 'defpact_majpow'] = d2.loc[within2, 'defpact_majpow'].fillna(0)

    # ── Merge into panel ──────────────────────────────────────────────────────
    df_panel = df_panel.drop(columns=['defpact_onset', 'defpact_majpow_onset'], errors='ignore')
    df_panel = df_panel.merge(
        d1[['conflict_id', 'atop_defensive']].rename(columns={'atop_defensive': 'defpact_onset'}),
        on='conflict_id', how='left'
    )
    df_panel = df_panel.merge(
        d2[['conflict_id', 'defpact_majpow']].rename(columns={'defpact_majpow': 'defpact_majpow_onset'}),
        on='conflict_id', how='left'
    )

    c = df_panel.drop_duplicates('conflict_id')
    print(f"defpact_onset:        1={( c['defpact_onset']==1).sum()}  "
          f"0={(c['defpact_onset']==0).sum()}  NaN={c['defpact_onset'].isna().sum()}")
    print(f"defpact_majpow_onset: 1={(c['defpact_majpow_onset']==1).sum()}  "
          f"0={(c['defpact_majpow_onset']==0).sum()}  NaN={c['defpact_majpow_onset'].isna().sum()}")

    return df_panel


# ── SHARED HELPER ────────────────────────────────────────────────────────────

def _onset_footprint(df_panel, ged_path):
    """
    Return onset DataFrame with columns: conflict_id, start_date,
    start_date_quarter, onset_year, onset_cells (set of priogrid_gid).

    Fallback: if a conflict has no GED events in its onset quarter
    (e.g. GED coverage begins after the recorded start_date), use the
    earliest quarter in which any GED event appears for that conflict.
    """
    ged = pd.read_csv(ged_path, low_memory=False,
                      usecols=['conflict_new_id', 'date_start', 'priogrid_gid'])
    ged = ged[ged['conflict_new_id'].isin(df_panel['conflict_id'].unique())]
    ged['date_start']         = pd.to_datetime(ged['date_start'], format='mixed')
    ged['date_start_quarter'] = ged['date_start'].dt.to_period('Q')

    onset = (
        df_panel.drop_duplicates('conflict_id')
        [['conflict_id', 'start_date']]
        .copy()
    )
    onset['start_date_quarter'] = pd.PeriodIndex(onset['start_date'], freq='M').asfreq('Q')
    onset['onset_year']         = onset['start_date'].str[:4].astype(int)

    ged_m     = ged.merge(onset[['conflict_id', 'start_date_quarter']],
                          left_on='conflict_new_id', right_on='conflict_id')
    ged_onset = ged_m[ged_m['date_start_quarter'] == ged_m['start_date_quarter']]
    footprint = (
        ged_onset.groupby('conflict_id')['priogrid_gid']
        .apply(set)
        .reset_index(name='onset_cells')
    )

    # Fallback for conflicts with no onset-quarter GED events
    missing = set(onset['conflict_id']) - set(footprint['conflict_id'])
    if missing:
        ged_miss  = ged_m[ged_m['conflict_id'].isin(missing)].copy()
        earliest  = (ged_miss.groupby('conflict_id')['date_start_quarter']
                     .min().reset_index(name='first_q'))
        ged_miss  = ged_miss.merge(earliest, on='conflict_id')
        ged_miss  = ged_miss[ged_miss['date_start_quarter'] == ged_miss['first_q']]
        fallback  = (ged_miss.groupby('conflict_id')['priogrid_gid']
                     .apply(set).reset_index(name='onset_cells'))
        footprint = pd.concat([footprint, fallback], ignore_index=True)
        print(f"  [fallback] {len(missing)} conflict(s) with no onset-quarter GED events "
              f"→ used earliest available quarter: {sorted(missing)}")

    return onset.merge(footprint, on='conflict_id', how='left')


# ── LOOT ONSET ───────────────────────────────────────────────────────────────

# Resource column names in PRIO-GRID files
_RES_Y = ['petroleum_y', 'diamsec_y', 'diamprim_y', 'gem_y',
           'drug_y', 'goldplacer_y', 'goldvein_y', 'goldsurface_y']
_RES_S = ['petroleum_s', 'diamsec_s', 'diamprim_s', 'gem_s',
           'goldplacer_s', 'goldvein_s', 'goldsurface_s']
_PRIO_YEARLY_END = 2014  # last year in the downloaded PRIO-GRID yearly file


def build_loot_onset(df_panel, ged_path, prio_static_path, prio_yearly_path):
    """
    Add loot_onset_strict and loot_onset to df_panel.

    Parameters
    ----------
    df_panel : pd.DataFrame
        Conflict panel with columns: conflict_id, start_date.
    ged_path : str
        Path to UCDP GED CSV (needs conflict_new_id, date_start, priogrid_gid).
    prio_static_path : str
        Path to PRIO-GRID Static Variables CSV.
    prio_yearly_path : str
        Path to PRIO-GRID Yearly Variables CSV (1989–2014).

    Returns
    -------
    pd.DataFrame
        df_panel with loot_onset_strict and loot_onset columns added.
    """
    # ── 1. GED onset footprint ────────────────────────────────────────────────
    onset     = _onset_footprint(df_panel, ged_path)
    onset_exp = (
        onset.explode('onset_cells')
        .rename(columns={'onset_cells': 'gid'})
        .dropna(subset=['gid'])
        .copy()
    )
    onset_exp['gid']         = onset_exp['gid'].astype(int)
    onset_exp['lookup_year'] = onset_exp['onset_year'].clip(upper=_PRIO_YEARLY_END).astype(int)

    # ── 2. Yearly resources: ffill within gid, join at onset year ────────────
    yr_cols = pd.read_csv(prio_yearly_path, nrows=0).columns.tolist()
    avail_y = [c for c in _RES_Y if c in yr_cols]
    yearly  = pd.read_csv(prio_yearly_path, usecols=['gid', 'year'] + avail_y)
    yearly  = yearly.sort_values(['gid', 'year'])
    yearly[avail_y] = yearly.groupby('gid')[avail_y].ffill()

    yr_merge    = onset_exp.merge(
        yearly[['gid', 'year'] + avail_y],
        left_on=['gid', 'lookup_year'], right_on=['gid', 'year'],
        how='left'
    )
    loot_strict = (
        yr_merge.groupby('conflict_id')[avail_y]
        .max().fillna(0).gt(0).any(axis=1).astype(int)
        .reset_index(name='loot_onset_strict')
    )

    # ── 3. Static resources ───────────────────────────────────────────────────
    s_cols  = pd.read_csv(prio_static_path, nrows=0).columns.tolist()
    avail_s = [c for c in _RES_S if c in s_cols]
    static  = pd.read_csv(prio_static_path, usecols=['gid'] + avail_s)

    s_merge     = onset_exp.merge(static, on='gid', how='left')
    loot_static = (
        s_merge.groupby('conflict_id')[avail_s]
        .max().fillna(0).gt(0).any(axis=1).astype(int)
        .reset_index(name='_has_static')
    )

    # ── 4. Combine and merge ──────────────────────────────────────────────────
    loot = loot_strict.merge(loot_static, on='conflict_id', how='outer').fillna(0)
    loot['loot_onset'] = (
        (loot['loot_onset_strict'] == 1) | (loot['_has_static'] == 1)
    ).astype(int)
    loot = loot.drop(columns='_has_static')

    df_panel = df_panel.drop(columns=['loot_onset_strict', 'loot_onset'], errors='ignore')
    df_panel = df_panel.merge(loot, on='conflict_id', how='left')

    cl = df_panel.drop_duplicates('conflict_id')
    print(f"loot_onset_strict: 1={(cl['loot_onset_strict']==1).sum():3}  "
          f"0={(cl['loot_onset_strict']==0).sum():3}  "
          f"NaN={cl['loot_onset_strict'].isna().sum()}")
    print(f"loot_onset:        1={(cl['loot_onset']==1).sum():3}  "
          f"0={(cl['loot_onset']==0).sum():3}  "
          f"NaN={cl['loot_onset'].isna().sum()}")

    return df_panel


# ── DISTANCE ONSET ────────────────────────────────────────────────────────────

def build_distance_onset(df_panel, ged_path, prio_yearly_path):
    """
    Add bdist_onset and capdist_onset to df_panel.

    Both variables are means over GED onset-quarter cells:
      bdist_onset  — mean distance (km) to nearest national border
      capdist_onset — mean distance (km) to country capital

    Low bdist_onset → conflict near a border (cross-border sanctuary risk).
    High capdist_onset → conflict far from capital (weak state reach).

    Source: PRIO-GRID 2.0 Yearly Variables (bdist3, capdist), 1989–2014.
    Post-2014 conflicts use 2014 values (borders/capitals change slowly).
    """
    # ── 1. GED onset footprint ────────────────────────────────────────────────
    onset     = _onset_footprint(df_panel, ged_path)
    onset_exp = (
        onset.explode('onset_cells')
        .rename(columns={'onset_cells': 'gid'})
        .dropna(subset=['gid'])
        .copy()
    )
    onset_exp['gid']         = onset_exp['gid'].astype(int)
    onset_exp['lookup_year'] = onset_exp['onset_year'].clip(upper=_PRIO_YEARLY_END).astype(int)

    # ── 2. PRIO-GRID distance variables at onset year ─────────────────────────
    yearly = pd.read_csv(prio_yearly_path, usecols=['gid', 'year', 'bdist3', 'capdist'])

    merged = onset_exp.merge(
        yearly, left_on=['gid', 'lookup_year'], right_on=['gid', 'year'],
        how='left'
    )

    # ── 3. Average over onset cells ───────────────────────────────────────────
    dist = (
        merged.groupby('conflict_id')[['bdist3', 'capdist']]
        .mean()
        .reset_index()
        .rename(columns={'bdist3': 'bdist_onset', 'capdist': 'capdist_onset'})
    )

    df_panel = df_panel.drop(columns=['bdist_onset', 'capdist_onset'], errors='ignore')
    df_panel = df_panel.merge(dist, on='conflict_id', how='left')

    cl = df_panel.drop_duplicates('conflict_id')
    print(f"bdist_onset   — mean={cl['bdist_onset'].mean():.1f} km  "
          f"NaN={cl['bdist_onset'].isna().sum()}")
    print(f"capdist_onset — mean={cl['capdist_onset'].mean():.1f} km  "
          f"NaN={cl['capdist_onset'].isna().sum()}")

    return df_panel


# ── MOUNTAINS ONSET ──────────────────────────────────────────────────────────

def build_mountains_onset(df_panel, ged_path, prio_static_path):
    """
    Add mountains_onset to df_panel.

    mountains_onset is the mean of PRIO-GRID `mountains_mean` (share of cell
    that is mountainous, Weidmann 2009) across the conflict's onset-quarter
    GED cells. High values indicate rough terrain — associated with rebel
    sanctuary and conflict persistence.

    Source: PRIO-GRID 2.0 Static Variables (time-invariant; no year lookup).

    Parameters
    ----------
    df_panel : pd.DataFrame
        Conflict panel with columns: conflict_id, start_date.
    ged_path : str
        Path to UCDP GED CSV (needs conflict_new_id, date_start, priogrid_gid).
    prio_static_path : str
        Path to PRIO-GRID Static Variables CSV (needs gid, mountains_mean).

    Returns
    -------
    pd.DataFrame
        df_panel with mountains_onset column added.
    """
    # ── 1. GED onset footprint ────────────────────────────────────────────────
    onset     = _onset_footprint(df_panel, ged_path)
    onset_exp = (
        onset.explode('onset_cells')
        .rename(columns={'onset_cells': 'gid'})
        .dropna(subset=['gid'])
        .copy()
    )
    onset_exp['gid'] = onset_exp['gid'].astype(int)

    # ── 2. Static mountains_mean: time-invariant, join directly on gid ────────
    static = pd.read_csv(prio_static_path, usecols=['gid', 'mountains_mean'])

    merged = onset_exp.merge(static, on='gid', how='left')
    # NaN in mountains_mean → coastal/oceanic cells with no terrain data → treat as 0
    merged['mountains_mean'] = merged['mountains_mean'].fillna(0)

    mountains = (
        merged.groupby('conflict_id')['mountains_mean']
        .mean()
        .reset_index()
        .rename(columns={'mountains_mean': 'mountains_onset'})
    )

    df_panel = df_panel.drop(columns=['mountains_onset'], errors='ignore')
    df_panel = df_panel.merge(mountains, on='conflict_id', how='left')

    cl = df_panel.drop_duplicates('conflict_id')
    print(f"mountains_onset — mean={cl['mountains_onset'].mean():.3f}  "
          f"NaN={cl['mountains_onset'].isna().sum()}")

    return df_panel
