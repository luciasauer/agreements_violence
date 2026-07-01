import pandas as pd


# ============================================================
# AUXILIARY FUNCTION
# ============================================================

def fill_only_if_observed(series):
    """
    Fill missing values only if at least one value
    exists within the group.

    If all values are NaN, keep them as NaN.
    """

    if series.notna().sum() == 0:
        return series

    return series.ffill().bfill()


# ============================================================
# MAIN FUNCTION
# ============================================================

def build_faction_variables(
    df_panel,
    dyadic_path
):

    # --------------------------------------------------------
    # Load dyadic dataset
    # --------------------------------------------------------

    df_dyads = pd.read_csv(
        dyadic_path,
        low_memory=False
    )

    # --------------------------------------------------------
    # Count number of dyads per conflict-year
    # --------------------------------------------------------

    factions_yr = (
        df_dyads
        .groupby(
            ["conflict_id", "year"]
        )["dyad_id"]
        .nunique()
        .reset_index()
        .rename(
            columns={
                "dyad_id":
                "n_factions_dyadic"
            }
        )
    )

    # --------------------------------------------------------
    # Merge into panel
    # --------------------------------------------------------

    df_panel = df_panel.merge(
        factions_yr,
        on=["conflict_id", "year"],
        how="left"
    )

    # --------------------------------------------------------
    # Sort panel
    # --------------------------------------------------------

    df_panel = df_panel.sort_values(
        [
            'conflict_id',
            'year',
            'year_mo'
        ]
    )

    # --------------------------------------------------------
    # Fill n_factions within conflict-year
    # --------------------------------------------------------

    df_panel['n_factions'] = (
        df_panel
        .groupby(
            ['conflict_id', 'year']
        )['n_factions']
        .transform(fill_only_if_observed)
    )

    # --------------------------------------------------------
    # Combine measures
    # --------------------------------------------------------

    df_panel['n_factions_combined'] = (
        df_panel[
            [
                'n_factions',
                'n_factions_dyadic'
            ]
        ]
        .max(axis=1)
    )

    # --------------------------------------------------------
    # New rebel entry: dyads appearing for the first time
    # in this conflict-year (after conflict onset)
    # --------------------------------------------------------

    first_year = (
        df_dyads
        .groupby(['conflict_id', 'dyad_id'])['year']
        .min()
        .reset_index(name='first_year')
    )

    df_dyads = df_dyads.merge(first_year, on=['conflict_id', 'dyad_id'])

    new_entry = (
        df_dyads[df_dyads['year'] == df_dyads['first_year']]
        .groupby(['conflict_id', 'year'])['dyad_id']
        .nunique()
        .reset_index(name='new_rebel_entry')
    )

    df_panel = df_panel.merge(new_entry, on=['conflict_id', 'year'], how='left')
    df_panel['new_rebel_entry'] = df_panel['new_rebel_entry'].fillna(0).astype(int)

    return df_panel