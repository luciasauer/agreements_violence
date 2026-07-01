import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_event_study_subplots_matched(
    df,
    treated_window_id,
    outcome_col="log_best",
    window_col="window_id",
    matched_col="matched_treated_window_id",
    t_col="window_t",
    iso_col="isocode",
    date_col="year_mo",
    treat_time=18,
    window=18,
    max_controls=6,
    marker_every=2,
):
    """
    Plots a treated WINDOW (by window_id) against each matched control WINDOW
    in separate subplots, aligned in event time (t - treat_time).

    Assumes:
      - window_t is 0..36
      - treat happens at treat_time (default 18)
      - controls have matched_treated_window_id == treated_window_id
    """

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # ---- treated window (ONLY that window_id) ----
    df_treat = df[df[window_col] == treated_window_id].copy()
    if df_treat.empty:
        raise ValueError(f"No rows found for treated_window_id={treated_window_id}")

    df_treat = df_treat.sort_values(t_col)
    df_treat["event_t"] = df_treat[t_col] - treat_time
    df_treat = df_treat[df_treat["event_t"].between(-window, window)]

    # label for treated from the event month (t=treat_time) if exists
    treat_row = df_treat.loc[df_treat[t_col] == treat_time]
    treated_iso = treat_row[iso_col].iloc[0] if not treat_row.empty else df_treat[iso_col].iloc[0]
    treated_date = treat_row[date_col].iloc[0] if not treat_row.empty else pd.NaT
    treated_label = (
        f"Treated {treated_iso}-{treated_date.strftime('%Y-%m')}"
        if pd.notna(treated_date)
        else f"Treated {treated_iso}"
    )

    # ---- matched control windows (by matched_treated_window_id) ----
    df_controls_at = df[(df[matched_col] == treated_window_id)].copy()
    if df_controls_at.empty:
        raise ValueError(f"No controls found with {matched_col} == {treated_window_id}")

    control_window_ids = (
        df_controls_at[window_col].dropna().unique().tolist()
    )
    control_window_ids = control_window_ids[:max_controls]

    n_controls = len(control_window_ids)
    fig, axes = plt.subplots(
        n_controls, 1,
        figsize=(10, 3 * n_controls),
        sharex=True,
        sharey=True
    )
    if n_controls == 1:
        axes = [axes]

    # global y-lims (avoid each panel jumping)
    combined = [df_treat]
    for cw in control_window_ids:
        d = df[df[window_col] == cw].copy()
        d["event_t"] = d[t_col] - treat_time
        d = d[d["event_t"].between(-window, window)]
        combined.append(d)
    comb_df = pd.concat(combined, axis=0, ignore_index=True)

    y_min = np.nanpercentile(comb_df[outcome_col], 2)
    y_max = np.nanpercentile(comb_df[outcome_col], 98)
    pad = 0.1 * (y_max - y_min) if y_max > y_min else 0.5
    ylims = (y_min - pad, y_max + pad)

    # helper for markers
    def _markevery(n):
        return max(1, int(n // (2 * window / marker_every + 1)))  # conservative
    # simpler: fixed spacing in x
    markevery = max(1, marker_every)

    for ax, cw in zip(axes, control_window_ids):
        df_c = df[df[window_col] == cw].copy()
        df_c = df_c.sort_values(t_col)
        df_c["event_t"] = df_c[t_col] - treat_time
        df_c = df_c[df_c["event_t"].between(-window, window)]

        c_row = df_c.loc[df_c[t_col] == treat_time]
        c_iso = c_row[iso_col].iloc[0] if not c_row.empty else df_c[iso_col].iloc[0]
        c_date = c_row[date_col].iloc[0] if not c_row.empty else pd.NaT
        c_label = (
            f"Control {c_iso}-{c_date.strftime('%Y-%m')}"
            if pd.notna(c_date)
            else f"Control {c_iso}"
        )

        # Treated
        ax.plot(
            df_treat["event_t"], df_treat[outcome_col],
            color="black", linewidth=2,
            marker="o", markersize=4, markevery=markevery,
            label=treated_label
        )

        # Control
        ax.plot(
            df_c["event_t"], df_c[outcome_col],
            color="grey", linewidth=2, linestyle="--", alpha=0.9,
            marker="o", markersize=4, markevery=markevery,
            label=c_label
        )

        ax.axvline(0, color="red", linestyle="--", linewidth=1)
        ax.set_ylabel("fatalities (log)", fontsize=14)
        #ax.set_ylim(*ylims)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(False)
        ax.margins(x=0)

        ax.legend(frameon=False, loc="upper right", fontsize=13, handlelength=2.5)

        ax.tick_params(axis="x", labelsize=13)
        ax.tick_params(axis="y", labelsize=13)

    axes[-1].set_xlabel("months to agreement", fontsize=14)
    axes[-1].set_xticks(list(range(-window, window + 1, 6)))

    plt.tight_layout()
    plt.show()