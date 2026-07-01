import pandas as pd
import numpy as np


def calculate_experience(pair_id, start_year, history_df, delta):
    """Calculate the number of times the pair of actor fought before the start
    of the conflict. And apply a discount factor, so the times closer to the
    conflict are weighted more heavily.

    Args:
        pair_id (_type_): side_a_id and side_b_id sorted and combined in a tuple
        start_year (_type_): year of the start of the conflict from panel
        history_df (_type_): dataframe containing the history of times the pair of actors fought
        delta (_type_): discount factor to apply to past fights

    Returns:
        _type_: the calculated experience value for each conflict - pair_id combination
    """
     # Keep only fights before the conflict onset
    previous_fights = history_df[
        (history_df["pair_id"] == pair_id) &
        (history_df["year"] < start_year)
    ]
    
     # If actors never fought before,
    # experience equals zero
    if len(previous_fights) == 0:
        return 0

    experience = 0
    
    # Compute discounted experience
    for year in previous_fights["year"]:

        distance = start_year - year

        experience += delta ** distance

    return experience

# ============================================================
# MAIN FUNCTION
# ============================================================

def build_experience(
    df_panel,
    dyadic_path,
    delta=0.95
):

    # --------------------------------------------------------
    # Load dyadic dataset
    # --------------------------------------------------------

    dyadic = pd.read_csv(
        dyadic_path,
        low_memory=False
    )

    # --------------------------------------------------------
    # Create pair_id
    # --------------------------------------------------------

    dyadic["pair_id"] = dyadic.apply(
        lambda x: tuple(
            sorted([
                str(x["side_a_id"]),
                str(x["side_b_id"])
            ])
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Conflict-level dataset
    # --------------------------------------------------------
    
    conflicts = df_panel[
        [
            "conflict_id",
            "start_date",
            "start_date_numeric"
        ]
    ].drop_duplicates()

    conflicts["start_year"] = (
        conflicts["start_date"]
        .str[:4]
        .astype(int)
    )

    # --------------------------------------------------------
    # Merge conflict onset into dyadic
    # --------------------------------------------------------

    conflict_start = df_panel[
        [
            "conflict_id",
            "start_year"
        ]
    ].drop_duplicates()

    dyadic = dyadic.merge(
        conflict_start,
        on="conflict_id",
        how="left"
    )

    # --------------------------------------------------------
    # Keep dyads active at onset
    # --------------------------------------------------------

    dyadic_initial = dyadic[
        dyadic["year"] <= dyadic["start_year"]
    ]

    # --------------------------------------------------------
    # Identify actor pairs
    # --------------------------------------------------------

    actors = dyadic_initial[
        [
            "conflict_id",
            "side_a_id",
            "side_b_id",
            "pair_id"
        ]
    ].drop_duplicates()

    conflicts = conflicts.merge(
        actors,
        on="conflict_id",
        how="left"
    )

    # --------------------------------------------------------
    # Historical fighting data
    # --------------------------------------------------------

    history = dyadic[
        [
            "pair_id",
            "year"
        ]
    ].drop_duplicates()

    # --------------------------------------------------------
    # Compute experience
    # --------------------------------------------------------

    conflicts["experience"] = conflicts.apply(
        lambda x: calculate_experience(
            x["pair_id"],
            x["start_year"],
            history,
            delta
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Aggregate to conflict level
    # --------------------------------------------------------

    conflicts = (
        conflicts
        .groupby("conflict_id")["experience"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # Merge into panel
    # --------------------------------------------------------

    df_panel = df_panel.merge(
        conflicts,
        on="conflict_id",
        how="left"
    )

    return df_panel

