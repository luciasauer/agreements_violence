"""
build_termination_outcome.py
============================
Transformation layer for constructing termination outcome variables used in
the competing-risks survival analysis (src/3_survival_analysis/).

Purpose
-------
The survival analysis classifies each conflict into one of four mutually
exclusive exit states — first_agreement, censored, fade, not at risk — based
on three data sources: the conflict panel (GED-based spell window), the PA-X
database (agreement timing), and the UCDP Conflict Termination Dataset
(episode outcomes). Raw PA-X ever_agreement flags require two corrections
before they can serve as event indicators:

  1. Pre-GED fix: agreements signed before the first GED event fall outside
     the survival spell and must be reclassified as non-events.
  2. Post-GED fix: agreements arriving after the last GED event are kept only
     when the termination dataset confirms the conflict is still ongoing;
     otherwise a competing event dominates and ever_agreement is set to 0.

This module exposes a single entry point, build_termination_outcome(), that
applies both fixes and appends the derived columns directly to df_panel.  It
is designed to be called from pipeline notebooks in the same way that other
build_* functions under functions/ are called.

Output columns added to df_panel
---------------------------------
  agree_timing              'never_signed' | 'pre_ged' | 'post_ged' | 'during_ged'
  ever_agreement            corrected binary flag (replaces the original column)
  termination_outcome_label 'ongoing' or UCDP label (see OUTCOME_LABEL_MAP)
  cause_label               'first_agreement' | 'censored' | 'fade' | 'not at risk'
  end_year_ged              year of the last GED event
  end_year_term             year of the UCDP termination endpoint (NaN if ongoing)
  c_ependdate_term_out      raw c_ependdate from the Termination Dataset
  c_outcome_term_out        raw c_outcome code from the Termination Dataset

See also
--------
  0_outcome_construction.ipynb — narrative analysis with summary statistics
                                 and crosstabs that document the decision rules
                                 implemented here.
"""

import pandas as pd
import numpy as np


# ============================================================
# CONSTANTS
# ============================================================

OUTCOME_LABEL_MAP = {
    1.0: "Peace agreement",
    2.0: "Ceasefire",
    3.0: "Victory (govt)",
    4.0: "Victory (rebels)",
    5.0: "Low activity",
    6.0: "Actor ceases to exist",
}

CAUSES_MAP = {
    "ongoing":               "censored",
    "Peace agreement":       "fade",
    "Ceasefire":             "fade",
    "Low activity":          "fade",
    "Victory (govt)":        "not at risk",
    "Victory (rebels)":      "not at risk",
    "Actor ceases to exist": "not at risk",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _classify_agree_timing(row):
    """Classify the timing of a PA-X agreement relative to the GED spell window.

    Args:
        row: a conflict-level row with columns ever_agreement,
             first_agreement_date, start_date_numeric, end_date_numeric.

    Returns:
        str: one of 'never_signed', 'pre_ged', 'post_ged', 'during_ged'.
    """
    if row["ever_agreement"] == 0:
        return "never_signed"
    if row["first_agreement_date"] < row["start_date_numeric"]:
        return "pre_ged"
    if row["first_agreement_date"] > row["end_date_numeric"]:
        return "post_ged"
    return "during_ged"


def _extract_last_term_row(df_term, conflict_ids):
    """Extract the last calendar-year row per conflict_id from the termination dataset.

    The UCDP Conflict Termination Dataset has one row per (conflict_id, year).
    Taking the maximum-year row captures: the terminal year of the last episode
    for concluded conflicts (c_epterm=1, c_ependdate filled) and the most recent
    year of an open episode for ongoing conflicts (c_epterm=0, c_ependdate NaN).

    Args:
        df_term (pd.DataFrame): full UCDP Conflict Termination Dataset.
        conflict_ids (array-like): conflict_id values to filter to.

    Returns:
        pd.DataFrame: one row per conflict_id with columns
            conflict_id, year_term_out, c_ependdate_term_out,
            c_outcome_term_out, c_epterm_term_out.
    """
    last_term = (
        df_term[df_term["conflict_id"].isin(conflict_ids)]
        .sort_values(["conflict_id", "year"])
        .drop_duplicates("conflict_id", keep="last")
        [["conflict_id", "year", "c_ependdate", "c_outcome", "c_epterm"]]
        .rename(columns={
            "year":        "year_term_out",
            "c_ependdate": "c_ependdate_term_out",
            "c_outcome":   "c_outcome_term_out",
            "c_epterm":    "c_epterm_term_out",
        })
    )
    # Some rows store a whitespace string instead of NaN; normalise to NaN.
    last_term["c_ependdate_term_out"] = (
        last_term["c_ependdate_term_out"].replace(" ", np.nan)
    )
    return last_term


def _assign_termination_label(end_year_ged, end_year_term, c_outcome):
    """Map (end_year_ged, end_year_term, c_outcome) to a termination outcome label.

    Decision rule:
      - No termination endpoint (NaN end_year_term) → 'ongoing'
      - GED end year equals termination end year and c_outcome is valid → OUTCOME_LABEL_MAP label
      - GED end year equals termination end year but c_outcome is NaN → 'ongoing'
      - GED end year exceeds termination end year → 'ongoing'
        (GED records sub-threshold activity for recognized dyads beyond the last
        UCDP/PRIO active episode, indicating the conflict was not conclusively
        terminated at the date recorded by the Termination Dataset)

    Args:
        end_year_ged (int): year of the last GED event in the panel.
        end_year_term (float or NaN): year of c_ependdate from the Termination Dataset.
        c_outcome (float or NaN): raw c_outcome code from the Termination Dataset.

    Returns:
        str: termination outcome label.
    """
    if pd.isna(end_year_term):
        return "ongoing"
    if end_year_ged == end_year_term:
        if pd.isna(c_outcome):
            return "ongoing"
        return OUTCOME_LABEL_MAP.get(c_outcome, "ongoing")
    return "ongoing"


# ============================================================
# MAIN FUNCTION
# ============================================================

def build_termination_outcome(df_panel, term_path):
    """Add termination outcome columns to the conflict panel.

    Implements the decision logic from 0_outcome_construction.ipynb as a
    transformation layer. Modifies ever_agreement in place (applying pre-GED
    and post-GED correction rules) and adds new conflict-level columns.

    New columns added to df_panel:
        agree_timing              — 'never_signed' | 'pre_ged' | 'post_ged' | 'during_ged'
        termination_outcome_label — 'ongoing' or UCDP termination label (see OUTCOME_LABEL_MAP)
        cause_label               — 'first_agreement' | 'censored' | 'fade' | 'not at risk'
        end_year_ged              — year of last GED event (int)
        end_year_term             — year of UCDP termination endpoint (float, NaN if ongoing)
        c_ependdate_term_out      — raw c_ependdate from Termination Dataset (last episode)
        c_outcome_term_out        — raw c_outcome code from Termination Dataset (last episode)

    ever_agreement is also updated: pre-GED and competing post-GED signers are
    reclassified to 0.

    Args:
        df_panel (pd.DataFrame): conflict-month panel with columns conflict_id,
            start_date, end_date, start_date_numeric, end_date_numeric,
            ever_agreement, first_agreement_date.
        term_path (str): path to the UCDP Conflict Termination Dataset CSV.

    Returns:
        pd.DataFrame: df_panel with new columns added and ever_agreement updated.
    """

    # --------------------------------------------------------
    # Collapse to conflict level
    # --------------------------------------------------------

    cl = (
        df_panel
        .drop_duplicates("conflict_id")
        [[
            "conflict_id",
            "start_date",
            "end_date",
            "start_date_numeric",
            "end_date_numeric",
            "ever_agreement",
            "first_agreement_date",
        ]]
        .copy()
    )

    # --------------------------------------------------------
    # Classify agreement timing relative to the GED window
    # --------------------------------------------------------

    cl["agree_timing"] = cl.apply(_classify_agree_timing, axis=1)

    # --------------------------------------------------------
    # Pre-GED fix: PA-X agreement predates first GED event
    # → the conflict is not a signer within the survival spell
    # --------------------------------------------------------

    cl.loc[cl["agree_timing"] == "pre_ged", "ever_agreement"] = 0

    # --------------------------------------------------------
    # Load termination dataset and extract last episode row
    # --------------------------------------------------------

    df_term = pd.read_csv(term_path, low_memory=False)
    last_term = _extract_last_term_row(df_term, cl["conflict_id"].unique())

    # --------------------------------------------------------
    # Merge termination data and extract comparison years
    # --------------------------------------------------------

    cl = cl.merge(last_term, on="conflict_id", how="left")

    cl["end_year_ged"] = cl["end_date"].str[:4].astype(int)
    cl["end_year_term"] = pd.to_datetime(
        cl["c_ependdate_term_out"], errors="coerce"
    ).dt.year

    # --------------------------------------------------------
    # Assign termination outcome label
    # --------------------------------------------------------

    cl["termination_outcome_label"] = cl.apply(
        lambda row: _assign_termination_label(
            row["end_year_ged"],
            row["end_year_term"],
            row["c_outcome_term_out"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Post-GED fix: competing event dominates when the conflict
    # already exited the risk set before the PA-X agreement arrived
    # --------------------------------------------------------

    post_competing = (
        (cl["agree_timing"] == "post_ged") &
        (cl["termination_outcome_label"] != "ongoing")
    )
    cl.loc[post_competing, "ever_agreement"] = 0

    # --------------------------------------------------------
    # Assign cause label
    # --------------------------------------------------------

    cl["cause_label"] = np.where(
        cl["ever_agreement"] == 1,
        "first_agreement",
        cl["termination_outcome_label"].map(CAUSES_MAP),
    )

    # --------------------------------------------------------
    # Merge conflict-level columns back into the panel
    # --------------------------------------------------------

    new_cols = [
        "conflict_id",
        "ever_agreement",
        "agree_timing",
        "termination_outcome_label",
        "cause_label",
        "end_year_ged",
        "end_year_term",
        "c_ependdate_term_out",
        "c_outcome_term_out",
    ]

    # Drop existing ever_agreement to replace it with the adjusted version.
    df_panel = df_panel.drop(columns=["ever_agreement"], errors="ignore")
    df_panel = df_panel.merge(cl[new_cols], on="conflict_id", how="left")

    return df_panel
