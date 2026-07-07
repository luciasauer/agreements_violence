"""
build_termination_outcome.py
============================
Transformation layer for constructing termination outcome variables used in
the competing-risks survival analysis (src/3_survival_analysis/).

Spell logic
-----------
The survival analysis models time to first peace agreement as a discrete-time
competing-risks process. Each conflict spell ends at the earliest of:

  (i)  First agreement signed — focal event (ever_agreement = 1).
  (ii) Military victory or fade-out before any agreement — competing risk
       (ever_agreement = 0; cause_label = 'not at risk' or 'fade').
  (iii) Data end with conflict still active and unsigned — censoring
       (ever_agreement = 0; cause_label = 'censored').

Signing is an event, not a termination. A conflict that signs first and is
won later is a signer; its later military fate is a separate durability
question. Competing risks are terminations-before-signing only.

Correction rules applied to PA-X ever_agreement
------------------------------------------------
  Step 0 — Pre-GED fix:
    Agreement signed before the first GED event falls outside the survival
    spell → reclassified as non-signer (ever_agreement = 0).

  Step 5 — Competing-event fix (signers only):
    For conflicts with a UCDP termination endpoint (c_ependdate not NaN),
    the termination date is compared to the first-agreement date:
      · first_agreement_date  > c_ependdate → competing event occurred first;
        conflict exited the risk set before signing → reclassified as non-signer.
      · first_agreement_date <= c_ependdate → signing wins; same-month counts
        as signing by convention → kept as signer.
      · c_ependdate is NaN (episode ongoing in UCDP) → conflict still open;
        agreement is the exit event → kept as signer, even if it arrives after
        the last GED event.

Spell endpoint correction for non-signers (Step 6)
----------------------------------------------------
For non-signers where GED activity extends beyond the UCDP termination date
(end_date_ged > c_ependdate), trailing sub-threshold GED events do not represent
continued risk. The spell is truncated at c_ependdate and the termination outcome
label is taken from c_outcome. This is stored in effective_end_date.

Output columns added to df_panel
---------------------------------
  ever_agreement            corrected binary (replaces original column)
  first_agreement_date      corrected numeric (0 for reclassified non-signers)
  agree_timing              diagnostic: 'never_signed' | 'pre_ged' |
                            'competing_event_first' | 'post_ged_ongoing' |
                            'during_ged'
  termination_outcome_label 'ongoing' or UCDP outcome label (NaN for signers)
  cause_label               'first_agreement' | 'censored' | 'fade' | 'not at risk'
  effective_end_date        spell endpoint in YYYY-MM:
                              during_ged signers  → first_agreement_date (YYYY-MM)
                              ucdp_only signers   → c_ependdate (set in Step 6c)
                              fade / not at risk  → c_ependdate if GED > term, else end_date
                              censored            → end_date
  end_year_ged              year of last GED event (diagnostic)
  end_year_term             year of UCDP termination endpoint (NaN if ongoing, diagnostic)
  c_ependdate_term_out      raw c_ependdate from Termination Dataset
  c_outcome_term_out        raw c_outcome code from Termination Dataset
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

# Non-signers labelled "ongoing" (c_ependdate = NaN) whose last GED event
# predates this cutoff are reclassified as "Low activity" (→ cause_label = "fade").
# Extended absence of GED activity without a recorded termination indicates silent
# cessation rather than an actively ongoing conflict.
# Affected conflicts (3): Romania 370 (1989-12), Bosnia-Herzegovina 389 (1995-12),
# Sudan 11344 (2011-06). Cutoff chosen as 2 years before data end (2024-12).
STALE_GED_CUTOFF = "2022-01"


# ============================================================
# HELPERS — DATE CONVERSION
# ============================================================

def _ym_str_to_numeric(ym_str):
    """Convert a 'YYYY-MM' string to year*12 + (month-1).

    This matches the numeric index used for start_date_numeric,
    end_date_numeric, and first_agreement_date in the conflict panel.
    Returns NaN for invalid or missing input.
    """
    try:
        y, m = str(ym_str)[:7].split("-")
        return int(y) * 12 + int(m) - 1
    except Exception:
        return np.nan


def _date_to_ym_numeric(date_str):
    """Convert a 'YYYY-MM-DD' date string to year*12 + (month-1).

    Returns NaN for invalid or missing input.
    """
    dt = pd.to_datetime(date_str, errors="coerce")
    if pd.isna(dt):
        return np.nan
    return dt.year * 12 + (dt.month - 1)


# ============================================================
# HELPERS — TERMINATION DATA
# ============================================================

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
    # Normalise whitespace-only strings to NaN.
    last_term["c_ependdate_term_out"] = (
        last_term["c_ependdate_term_out"].replace(" ", np.nan)
    )
    return last_term


# ============================================================
# HELPERS — CLASSIFICATION
# ============================================================

def _classify_agree_timing(row):
    """Classify agreement timing for diagnostics after all corrections.

    Uses the original ever_agreement / first_agreement_date values (before
    any reclassification) together with the final ever_agreement to label
    each conflict into one of five categories.

    Categories:
      never_signed          — no PA-X record from the start
      ucdp_only             — no PA-X record but UCDP records Peace agreement or Ceasefire
                              termination; reclassified as treated (Step 6c)
      pre_ged               — PA-X agreement predated first GED event (reclassified)
      competing_event_first — termination occurred before PA-X agreement (reclassified)
      post_ged_ongoing      — agreement after last GED event; conflict still open (kept)
      during_ged            — agreement within GED window and before term date (kept)
    """
    orig_ea  = row["_orig_ever_agreement"]
    orig_fad = row["_orig_first_agreement_date"]
    final_ea = row["ever_agreement"]

    if orig_ea == 0:
        if final_ea == 1:
            return "ucdp_only"
        return "never_signed"

    if orig_ea == 1 and final_ea == 0:
        if orig_fad < row["start_date_numeric"]:
            return "pre_ged"
        return "competing_event_first"

    # Kept as signer
    if orig_fad > row["_ged_end_numeric"]:
        return "post_ged_ongoing"
    return "during_ged"


def _assign_nonsigner_outcome(row):
    """Assign termination_outcome_label and effective_end_date for a non-signer row.

    Decision rule:
      - c_ependdate NaN                 → 'ongoing'; spell until GED end_date
      - GED end ≤ termination end       → c_outcome label; spell until GED end_date
      - GED end >  termination end      → c_outcome label; spell truncated to c_ependdate

    Args:
        row: conflict-level Series with _term_numeric, _ged_end_numeric,
             c_outcome_term_out, c_ependdate_term_out, end_date.

    Returns:
        pd.Series with keys termination_outcome_label and effective_end_date.
    """
    term_num  = row["_term_numeric"]
    ged_num   = row["_ged_end_numeric"]
    c_outcome = row["c_outcome_term_out"]
    end_date  = row["end_date"]

    if pd.isna(term_num):
        return pd.Series({
            "termination_outcome_label": "ongoing",
            "effective_end_date":        end_date,
        })

    label = (
        OUTCOME_LABEL_MAP.get(c_outcome, "ongoing")
        if not pd.isna(c_outcome) else "ongoing"
    )

    if ged_num <= term_num:
        # GED end aligns with termination → spell runs to GED end
        return pd.Series({
            "termination_outcome_label": label,
            "effective_end_date":        end_date,
        })
    else:
        # GED extends beyond termination → truncate spell at termination date
        term_ym = pd.to_datetime(row["c_ependdate_term_out"]).strftime("%Y-%m")
        return pd.Series({
            "termination_outcome_label": label,
            "effective_end_date":        term_ym,
        })


# ============================================================
# MAIN FUNCTION
# ============================================================

def build_termination_outcome(df_panel, term_path):
    """Add termination outcome columns to the conflict panel.

    Applies the competing-risks spell logic described in the module docstring.
    Corrects ever_agreement and first_agreement_date in place and appends
    all derived columns to df_panel.

    Args:
        df_panel (pd.DataFrame): conflict-month panel with columns conflict_id,
            start_date, end_date, start_date_numeric, end_date_numeric,
            ever_agreement, first_agreement_date.
        term_path (str): path to the UCDP Conflict Termination Dataset CSV.

    Returns:
        pd.DataFrame: df_panel with new columns added and ever_agreement /
            first_agreement_date updated.
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

    # Store originals for agree_timing diagnostic (before any modification).
    cl["_orig_ever_agreement"]       = cl["ever_agreement"]
    cl["_orig_first_agreement_date"] = cl["first_agreement_date"]

    # --------------------------------------------------------
    # Step 0 — Pre-GED fix
    # Agreement predates first GED event → outside the survival spell.
    # --------------------------------------------------------

    pre_ged = (
        (cl["ever_agreement"] == 1) &
        (cl["first_agreement_date"] < cl["start_date_numeric"])
    )
    cl.loc[pre_ged, "ever_agreement"]       = 0
    cl.loc[pre_ged, "first_agreement_date"] = 0

    # --------------------------------------------------------
    # Load termination dataset and extract last episode row
    # --------------------------------------------------------

    df_term   = pd.read_csv(term_path, low_memory=False)
    last_term = _extract_last_term_row(df_term, cl["conflict_id"].unique())
    cl        = cl.merge(last_term, on="conflict_id", how="left")

    # --------------------------------------------------------
    # Convert dates to the same numeric index for comparison
    # --------------------------------------------------------

    cl["_term_numeric"]    = cl["c_ependdate_term_out"].apply(_date_to_ym_numeric)
    cl["_ged_end_numeric"] = cl["end_date"].apply(_ym_str_to_numeric)

    # --------------------------------------------------------
    # Step 5 — Competing-event fix (signers only)
    # Compare first_agreement_date with _term_numeric.
    #   c_ependdate NaN          → keep as signer (conflict ongoing in UCDP)
    #   first_agreement > term   → competing event first → reclassify
    #   first_agreement <= term  → signing wins (same month = signing by convention)
    # --------------------------------------------------------

    competing_wins = (
        (cl["ever_agreement"] == 1) &
        cl["_term_numeric"].notna() &
        (cl["first_agreement_date"] > cl["_term_numeric"])
    )
    cl.loc[competing_wins, "ever_agreement"]       = 0
    cl.loc[competing_wins, "first_agreement_date"] = 0

    # --------------------------------------------------------
    # Step 6 — Non-signer: termination outcome + effective_end_date
    # --------------------------------------------------------

    non_signer_mask = cl["ever_agreement"] == 0

    nonsigner_results = (
        cl[non_signer_mask]
        .apply(_assign_nonsigner_outcome, axis=1)
    )

    cl["termination_outcome_label"] = None
    cl["effective_end_date"]        = cl["end_date"]   # default for signers

    cl.loc[non_signer_mask, "termination_outcome_label"] = (
        nonsigner_results["termination_outcome_label"].values
    )
    cl.loc[non_signer_mask, "effective_end_date"] = (
        nonsigner_results["effective_end_date"].values
    )

    # --------------------------------------------------------
    # Step 6b — Stale cessation override
    # Non-signers labelled "ongoing" (c_ependdate = NaN) whose last GED
    # event predates STALE_GED_CUTOFF → reclassify to "Low activity".
    # --------------------------------------------------------

    stale_cutoff_num = _ym_str_to_numeric(STALE_GED_CUTOFF)
    stale_mask = (
        non_signer_mask &
        (cl["termination_outcome_label"] == "ongoing") &
        (cl["_ged_end_numeric"] < stale_cutoff_num)
    )
    cl.loc[stale_mask, "termination_outcome_label"] = "Low activity"

    # --------------------------------------------------------
    # Step 6c — UCDP-only treated conflicts
    # Non-signers whose UCDP episode (termination outcome) ended via
    # Peace agreement or Ceasefire not captured by PA-X → reclassify as treated.
    # first_agreement_date is set to the UCDP termination month (_term_numeric).
    # effective_end_date is set to c_ependdate (the termination date).
    # --------------------------------------------------------

    ucdp_treated_mask = (
        non_signer_mask &
        cl["termination_outcome_label"].isin(["Peace agreement", "Ceasefire"])
    )
    cl.loc[ucdp_treated_mask, "ever_agreement"]       = 1
    cl.loc[ucdp_treated_mask, "first_agreement_date"] = cl.loc[ucdp_treated_mask, "_term_numeric"]
    cl.loc[ucdp_treated_mask, "effective_end_date"]   = (
        pd.to_datetime(cl.loc[ucdp_treated_mask, "c_ependdate_term_out"])
        .dt.strftime("%Y-%m")
    )

    # --------------------------------------------------------
    # Cause label
    # --------------------------------------------------------

    cl["cause_label"] = np.where(
        cl["ever_agreement"] == 1,
        "first_agreement",
        cl["termination_outcome_label"].map(CAUSES_MAP),
    )

    # --------------------------------------------------------
    # Diagnostic: fill termination_outcome_label for signers
    # cause_label is already set above; this fills the UCDP episode outcome
    # for signers so the column is non-null for all conflicts.
    # --------------------------------------------------------

    signer_mask = cl["ever_agreement"] == 1
    cl.loc[signer_mask, "termination_outcome_label"] = (
        cl.loc[signer_mask, "c_outcome_term_out"]
        .map(OUTCOME_LABEL_MAP)
        .fillna("ongoing")
    )

    # --------------------------------------------------------
    # Agree timing (diagnostic)
    # --------------------------------------------------------

    cl["agree_timing"] = cl.apply(_classify_agree_timing, axis=1)

    # --------------------------------------------------------
    # Step 7 — Fix effective_end_date for PA-X signers (during_ged)
    # After Steps 0–6c, effective_end_date for during_ged signers still
    # holds end_date (GED end), which may be years after the agreement.
    # Convert first_agreement_date (relative scale, 1=1989-01) to YYYY-MM
    # so that effective_end_date is the true spell endpoint for all conflicts.
    # ucdp_only signers already have effective_end_date = c_ependdate (Step 6c).
    # --------------------------------------------------------

    _BASE_PERIOD = pd.Period("1989-01", freq="M")
    # Only apply to true PA-X during_ged signers whose first_agreement_date
    # is still in relative scale (1 = 1989-01, max = end_date_numeric ≤ 432).
    # Conflicts reclassified by Step 6c (274, 390) have agree_timing='during_ged'
    # but first_agreement_date was set to _term_numeric (absolute, ≈ 24000);
    # their effective_end_date was already set correctly by Step 6c, so skip them.
    during_ged_mask = (
        (cl["agree_timing"] == "during_ged") &
        (cl["first_agreement_date"] <= cl["end_date_numeric"])
    )
    cl.loc[during_ged_mask, "effective_end_date"] = (
        cl.loc[during_ged_mask, "first_agreement_date"]
        .apply(lambda n: (_BASE_PERIOD + int(n) - 1).strftime("%Y-%m"))
    )

    # --------------------------------------------------------
    # Diagnostic year columns
    # --------------------------------------------------------

    cl["end_year_ged"]  = cl["end_date"].str[:4].astype(int)
    cl["end_year_term"] = pd.to_datetime(
        cl["c_ependdate_term_out"], errors="coerce"
    ).dt.year

    # --------------------------------------------------------
    # Merge conflict-level columns back into the panel
    # --------------------------------------------------------

    new_cols = [
        "conflict_id",
        "ever_agreement",
        "first_agreement_date",
        "agree_timing",
        "termination_outcome_label",
        "cause_label",
        "effective_end_date",
        "end_year_ged",
        "end_year_term",
        "c_ependdate_term_out",
        "c_outcome_term_out",
    ]

    df_panel = df_panel.drop(
        columns=["ever_agreement", "first_agreement_date"], errors="ignore"
    )
    df_panel = df_panel.merge(cl[new_cols], on="conflict_id", how="left")

    return df_panel
