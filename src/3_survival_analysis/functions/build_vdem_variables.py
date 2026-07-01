import pandas as pd
import numpy as np

# ============================================================
# VARIABLES TO IMPORT FROM V-DEM
# ============================================================

VDEM_COLS = [
    "country_name", "COWcode", "year",
    # Sovereignty/State → commitment proxies
    "v2svstterr",       # state territorial control
    "v2svdomaut",       # domestic autonomy
    "v2stfisccap",      # fiscal capacity
    "v2stcritrecadm",   # meritocracy in state appointments
    "v2stcritapparm",   # meritocracy in armed forces appointments
    "e_wbgi_pve",     # World Bank's Political Stability and Absence of Violence
    "e_wbgi_gee",     # World Bank's Government Effectiveness
    # Neopatrimonialism → personalist regime (reemplaza GWF)
    "v2x_neopat",       # neopatrimonial rule index ← la más importante
    "v2xnp_client",     # clientelism
    "v2xnp_pres",       # presidentialism
    "v2xnp_regcorr",    # regime corruption
    # Accountability → information proxies
    "v2x_horacc",       # horizontal accountability
    "v2x_jucon",        # judicial constraints on executive
    "v2xlg_legcon",     # legislative constraints on executive
    "v2x_regime",       # regime type (RoW ordinal),
    "v2cltrnslw",       # predictable enforcement (commitment proxy)    
    "v2clrspct",        # public administration capacity
    "v2juhcind",        # judicial independence (commitment proxy)
    "v2jucomp",         #judicial compliance (commitment proxy)
    #"v2exrescont",     # executive respects consitution
]

columns_to_rename = {
    "country_name":     "country",
    "COWcode":          "cow_code",
    "v2svstterr":       "vdem_state_territorial_control",
    "v2svdomaut":       "vdem_domestic_autonomy",
    "v2stfisccap":      "vdem_fiscal_capacity",
    "v2stcritrecadm":   "vdem_meritocracy_state",
    "v2stcritapparm":   "vdem_meritocracy_army",
    "v2x_neopat":       "vdem_neopatrimonial",      # ← proxy de personalismo
    "v2xnp_client":     "vdem_clientelism",
    "v2xnp_pres":       "vdem_presidentialism",
    "v2xnp_regcorr":    "vdem_regime_corruption",
    "v2x_horacc":       "vdem_horizontal_accountability",
    "v2x_jucon":        "vdem_judicial_constraints",
    "v2xlg_legcon":     "vdem_legislative_constraints",
    "v2x_regime":       "vdem_regime_type",
    "v2cltrnslw":       "vdem_predictable_enforcement",
    "v2clrspct":        "vdem_public_adm_capacity",
    "v2juhcind":        "vdem_judicial_independence",
    "v2jucomp":         "vdem_judicial_compliance",
    "e_wbgi_pve":     "vdem_wb_political_stability",
    "e_wbgi_gee":     "vdem_wb_government_effectiveness"
}

# ============================================================
# INDEPENDENCE YEARS
# ============================================================

# Define the year of independence for relevant countries to guide interpolation limits
INDEPENDENCE_YEAR = {
    # Ex-soviets: use bfill only for 1990
    "Armenia": 1991, "Azerbaijan": 1991, "Belarus": 1991,
    "Estonia": 1991, "Georgia": 1991, "Kazakhstan": 1991,
    "Kyrgyzstan": 1991, "Latvia": 1991, "Lithuania": 1991,
    "Moldova": 1991, "Tajikistan": 1991, "Turkmenistan": 1991,
    "Ukraine": 1991, "Uzbekistan": 1991,
    # Ex-Yugoslavia
    "Croatia": 1991, "Slovenia": 1991, "Montenegro": 2006,
    # others
    "Kosovo":      2008,
    "Timor-Leste": 2002,
    "Eritrea":     1993,
    "Namibia":     1990,
    # Never existed / disappeared → leave NaN
    "Somaliland":                  None,
    "South Yemen":                 None,
    "German Democratic Republic":  None,
}


# ============================================================
# AUXILIARY FUNCTION
# ============================================================
def fill_state_capacity(group, country_name):

    ind_year = INDEPENDENCE_YEAR.get(country_name, None)

    if ind_year is None:
        return group

    group["vdem_state_territorial_control"] = (
        group["vdem_state_territorial_control"]
        .bfill(limit=2)
    )

    mask = group["year"] >= ind_year

    group.loc[mask, "vdem_state_territorial_control"] = (
        group.loc[mask, "vdem_state_territorial_control"]
        .interpolate(method="linear")
        .ffill(limit=3)
    )

    pre_ind_mask = group["year"] < ind_year - 1

    group.loc[
        pre_ind_mask,
        "vdem_state_territorial_control"
    ] = np.nan

    return group

# ============================================================
# VARIABLES FOR ROLLING PRE-CONFLICT MEANS
# ============================================================

VDEM_ROLLING_VARS = [
    "vdem_state_territorial_control",
    "vdem_horizontal_accountability",
    "vdem_judicial_constraints",
    "vdem_legislative_constraints",
    "vdem_neopatrimonial",
    "vdem_clientelism",
    "vdem_predictable_enforcement",
    "vdem_wb_political_stability",
    "vdem_wb_government_effectiveness",
    "vdem_public_adm_capacity",

]

def add_rolling_pre_conflict_means(
    df_vdem: pd.DataFrame,
    variables: list = VDEM_ROLLING_VARS,
    window: int = 5,
) -> pd.DataFrame:
    """
    For each variable, compute the rolling mean over the previous
    'window' years (including the current year).

    At year t the new column contains mean(t-window, ..., t).
    When merged to the conflict panel at start_year, this gives
    the pre-conflict average without any data leakage.

    New columns are named: {var}_pre{window}y
    """
    df = df_vdem.copy()
    df = df.sort_values(["cow_code", "year"])

    for var in variables:
        col_name = f"{var}_pre{window}y"
        df[col_name] = (
            df.groupby("cow_code")[var]
            .transform(
                lambda x: x.rolling(window=window, min_periods=1)
                           .mean()
            )
        )

    return df


# ============================================================
# MAIN FUNCTION
# ============================================================

def build_vdem_dataset(vdem_path):

    df_vdem = pd.read_csv(
        vdem_path,
        usecols=VDEM_COLS,
        low_memory=False
    )

    # rename
    df_vdem = df_vdem.rename(columns=columns_to_rename)

    # keep years
    df_vdem = df_vdem[
        (df_vdem["year"] >= 1989-5)
        &
        (df_vdem["year"] <= 2025)
    ]

    # # fix Somaliland
    # df_vdem.loc[
    #     df_vdem['country'] == 'Somaliland',
    #     'cow_code'
    # ] = 520

    df_vdem = df_vdem.dropna(
        subset=['cow_code']
    )

    # interpolate state capacity
    df_vdem = (
        df_vdem
        .sort_values("year")
        .groupby("country", group_keys=False)
        .apply(
            lambda g:
            fill_state_capacity(
                g,
                g["country"].iloc[0]
            )
        )
    )

    # Add mean pre-conflict rolling
    df_vdem = add_rolling_pre_conflict_means(df_vdem)

    return df_vdem


# ============================================================
# MERGE FUNCTION
# ============================================================

def merge_vdem_to_panel(
    df_panel,
    df_vdem,
    VDEM_columns,
    ucdp_path
):

    # load UCDP
    df_ucdp = pd.read_csv(
        ucdp_path,
        low_memory=False
    )

    df_ucdp = df_ucdp.loc[
        df_ucdp['type_of_violence'] == 1
    ]

    df_ucdp = df_ucdp[
        [
            'conflict_new_id',
            'gwnoa',
            'gwnob'
        ]
    ].rename(columns={
        'conflict_new_id': 'conflict_id'
    }).drop_duplicates('conflict_id')

    # merge
    df_panel = df_panel.merge(
        df_ucdp,
        on=['conflict_id'],
        how='left'
    )

    # # fill gwno
    # df_panel[['gwnoa', 'gwnob']] = (
    #     df_panel.groupby('conflict_id')[
    #         ['gwnoa', 'gwnob']
    #     ]
    #     .transform(
    #         lambda x: x.ffill().bfill()
    #     )
    # )

    # special cases
    df_panel.loc[
        df_panel['gwnoa'] == '2;200;900',
        'gwnoa'
    ] = df_panel.loc[
        df_panel['gwnoa'] == '2;200;900',
        'gwnob'
    ]

    df_panel.loc[
        (
            df_panel['country']
            == 'Yemen (North Yemen)'
        )
        &
        (df_panel['year'] > 1990),
        'gwnoa'
    ] = 679

    df_panel['gwnoa'] = (
        df_panel['gwnoa']
        .astype(float)
    )



    # merge VDEM
    df_panel = df_panel.merge(
        df_vdem[VDEM_columns],
        left_on=['gwnoa', 'year'],
        right_on=['cow_code', 'year'],
        how='left'
    )

    return df_panel