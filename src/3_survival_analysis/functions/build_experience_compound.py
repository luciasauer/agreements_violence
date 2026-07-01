"""
build_experience.py
-------------------
Compute pre-conflict fighting experience as a proxy for information asymmetry.

Two levels of experience:
  1. Direct:     the exact same pair of actors fought before.
  2. Government: side_a (government) fought OTHER groups before — captures
                 information revealed to all actors through past conflicts.

Usage:
    from functions.build_experience import build_experience_expanded

    df_panel = build_experience_expanded(
        df_panel,
        dyadic_path = "../../data/input/ucdp/Dyadic_v25_1.csv",
        delta = 0.95,
        weight_direct = 1.0,
        weight_government = 0.5,
    )
"""

import pandas as pd
import numpy as np


# ── Discounted experience calculation ─────────────────────────────────────────

def _discounted_count(years, start_year, delta):
    """Sum of delta^(start_year - y) for each year y < start_year."""
    return sum(delta ** (start_year - y) for y in years if y < start_year)


# ── Original function (kept for backward compatibility) ───────────────────────

def build_experience(df_panel, dyadic_path, delta=0.95):
    """Original: only direct (same pair) experience."""
    return build_experience_expanded(
        df_panel, dyadic_path, delta,
        weight_direct=1.0, weight_government=0.0,
    )


# ── Expanded function ─────────────────────────────────────────────────────────

def build_experience_expanded(
    df_panel,
    dyadic_path,
    delta=0.95,
    weight_direct=1.0,
    weight_government=0.5,
):
    """
    Compute pre-conflict fighting experience at two levels.

    Direct experience: the exact pair (side_a, side_b) fought before.
    Government experience: side_a fought OTHER groups before — so the
    government revealed its type through other conflicts, and the rebel
    group could observe that.

    Both are discounted by delta^distance, where distance = start_year - year.

    The composite experience_total = weight_direct × direct + weight_government × government.
    Higher experience_total = lower information asymmetry.

    Parameters
    ----------
    df_panel : pd.DataFrame
        Conflict panel. Must contain: conflict_id, start_date.
    dyadic_path : str
        Path to UCDP Dyadic v25.1 CSV.
    delta : float
        Persistence/discount factor. Default: 0.95.
    weight_direct : float
        Weight for direct experience in composite. Default: 1.0.
    weight_government : float
        Weight for government experience in composite. Default: 0.5.

    Returns
    -------
    pd.DataFrame
        df_panel with new columns:
        - exp_direct       : discounted direct experience (same pair)
        - exp_government   : discounted government experience (side_a vs others)
        - experience_total : weighted composite
        - experience       : same as experience_total (backward compatible)
    """

    # ── Load dyadic data ──────────────────────────────────────────────────────
    dyadic = pd.read_csv(dyadic_path, low_memory=False)

    dyadic["pair_id"] = dyadic.apply(
        lambda x: tuple(sorted([str(x["side_a_id"]), str(x["side_b_id"])])),
        axis=1,
    )

    # ── Conflict metadata ─────────────────────────────────────────────────────
    conflicts = (
        df_panel[["conflict_id", "start_date"]]
        .drop_duplicates("conflict_id")
        .copy()
    )
    conflicts["start_year"] = pd.to_datetime(conflicts["start_date"]).dt.year

    # ── Merge start_year into dyadic ──────────────────────────────────────────
    dyadic = dyadic.merge(
        conflicts[["conflict_id", "start_year"]],
        on="conflict_id",
        how="left",
    )

    # ── Actors at onset (dyads active at or before start_year) ────────────────
    dyadic_onset = dyadic[dyadic["year"] <= dyadic["start_year"]]
    actors = (
        dyadic_onset[["conflict_id", "side_a_id", "side_b_id", "pair_id"]]
        .drop_duplicates()
    )

    # One conflict can have multiple dyads — we compute experience per dyad
    # then aggregate to conflict level (mean across dyads).
    conflict_dyads = conflicts.merge(actors, on="conflict_id", how="left")

    # ── Full fighting history ─────────────────────────────────────────────────
    history = dyadic[["pair_id", "side_a_id", "year"]].drop_duplicates()

    # ── Compute experience per conflict-dyad ──────────────────────────────────
    rows = []

    for _, row in conflict_dyads.iterrows():
        cid  = row["conflict_id"]
        sy   = row["start_year"]
        pid  = row["pair_id"]
        sa   = row["side_a_id"]

        # Skip if no dyad info (shouldn't happen, but just in case)
        if pd.isna(sa):
            rows.append({"conflict_id": cid, "exp_direct": 0, "exp_government": 0})
            continue

        # 1. DIRECT — same pair fought before
        direct_years = history.loc[
            (history["pair_id"] == pid) & (history["year"] < sy),
            "year",
        ].unique()
        exp_direct = _discounted_count(direct_years, sy, delta)

        # 2. GOVERNMENT — same side_a fought OTHER pairs before
        govt_years = history.loc[
            (history["side_a_id"] == sa) &
            (history["pair_id"] != pid) &
            (history["year"] < sy),
            "year",
        ].unique()
        exp_govt = _discounted_count(govt_years, sy, delta)

        rows.append({
            "conflict_id":    cid,
            "exp_direct":     exp_direct,
            "exp_government": exp_govt,
        })

    result = pd.DataFrame(rows)

    # ── Aggregate to conflict level (mean across dyads) ───────────────────────
    result = (
        result
        .groupby("conflict_id")[["exp_direct", "exp_government"]]
        .mean()
        .reset_index()
    )

    # ── Composite ─────────────────────────────────────────────────────────────
    result["experience_total"] = (
        weight_direct     * result["exp_direct"]
        + weight_government * result["exp_government"]
    )

    

    # ── Report ────────────────────────────────────────────────────────────────
    n = len(result)
    n_zero_direct = (result["exp_direct"] == 0).sum()
    n_zero_total  = (result["experience_total"] == 0).sum()
    print(
        f"Experience computed for {n} conflicts:\n"
        f"  exp_direct = 0 in {n_zero_direct}/{n} conflicts ({n_zero_direct/n:.0%})\n"
        f"  experience_total = 0 in {n_zero_total}/{n} conflicts ({n_zero_total/n:.0%})\n"
        f"  (fewer zeros = more variation for IA proxy)"
    )

    # ── Merge into panel ──────────────────────────────────────────────────────
    # Drop old experience columns if they exist
    drop_cols = [c for c in ["exp_direct", "exp_government", "experience_total"]
                 if c in df_panel.columns]
    if drop_cols:
        df_panel = df_panel.drop(columns=drop_cols)

    df_panel = df_panel.merge(result, on="conflict_id", how="left")

    return df_panel