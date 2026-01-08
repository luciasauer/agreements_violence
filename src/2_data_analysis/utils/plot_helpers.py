import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from . import plot_style


def plot_conflict_agreement(df, country, isocode, ax=None):
    data_country = df[df["isocode"] == isocode].copy()
    if data_country.empty:
        return ax

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    # main line
    sns.lineplot(
        data=data_country,
        x="year_mo",
        y="log_best",
        color="black",
        linewidth=2.5,
        ax=ax,
    )

    for _, row in data_country[data_country["agreement"] == 1].iterrows():
        ax.axvline(row["year_mo"], color="#90353B", linestyle="-", alpha=1, lw=2.5)

    # axis labels + title
    ax.set_title(f"{country}", fontsize=18, pad=12)
    ax.set_xlabel("", fontsize=16)
    ax.set_ylabel("fatalities (log)", fontsize=18)

    ax.tick_params(axis="x", labelsize=16)
    ax.tick_params(axis="y", labelsize=16)
    # clean borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # spines in black
    ax.spines["left"].set_color("black")
    ax.spines["bottom"].set_color("black")
    # no grid lines
    ax.grid(False)

    ax.set_xlim(data_country["year_mo"].min(), data_country["year_mo"].max())
    ax.margins(x=0)

    # Custom formatter: 1990m1 instead of 1990m01
    def custom_fmt(x, _pos):
        dt = mdates.num2date(x)
        return f"{dt.year}m{dt.month}"

    ax.xaxis.set_major_formatter(FuncFormatter(custom_fmt))
    return ax


def plot_agreement_mediation_event_studies(
    df,
    window=18,
    min_gap_multiplier=1,
    figsize=(12, 5),
    sharey=False,
    savepath=None,
    treatment="agreement",
):
    df = df.copy()

    # --- prepare integer-month index (cheap arithmetic) ---
    df["year_mo"] = pd.to_datetime(df["year_mo"])
    # ym_int = year * 12 + (month - 1), so Jan 1990 -> 1990*12 + 0
    df["ym_int"] = df["year_mo"].dt.year * 12 + (df["year_mo"].dt.month - 1)

    # quick dictionary of country panels to avoid repeated boolean indexing
    groups = {iso: g.sort_values("ym_int") for iso, g in df.groupby("isocode")}

    min_gap_months = int(min_gap_multiplier * window)

    # helper: find valid (non-overlapping according to min_gap_months) events for a given flag column
    def find_valid_events_first_per_window(flag_col):
        events = df.loc[df[flag_col] == 1, ["isocode", "year_mo", "ym_int"]]
        if events.empty:
            return pd.DataFrame(columns=["isocode", "year_mo", "ym_int"])

        events = events.sort_values(["isocode", "ym_int"])
        valid = []

        for iso, grp in events.groupby("isocode", sort=False):
            last_kept = None
            for _, r in grp.iterrows():
                if last_kept is None or (r["ym_int"] - last_kept) > min_gap_months:
                    valid.append(
                        {
                            "isocode": iso,
                            "year_mo": r["year_mo"],
                            "ym_int": int(r["ym_int"]),
                        }
                    )
                    last_kept = r["ym_int"]

        return pd.DataFrame(valid)

    valid_agreements = find_valid_events_first_per_window(treatment)

    # helper: align events and summarize mean + 95% CI
    def align_and_summarize(valid_events):
        aligned_list = []
        if valid_events.empty:
            return pd.DataFrame(
                columns=["event_time", "mean_log", "std_log", "n", "se", "ci_lower", "ci_upper"]
            )

        for _, ev in valid_events.iterrows():
            iso = ev["isocode"]
            ev_ym = ev["ym_int"]
            panel = groups.get(iso)
            if panel is None:
                continue
            # vectorized event_time (months)
            sub = panel.copy()
            sub["event_time"] = sub["ym_int"] - ev_ym
            sub = sub.loc[
                (sub["event_time"] >= -window) & (sub["event_time"] <= window),
                ["event_time", "log_best"],
            ]
            if not sub.empty:
                aligned_list.append(sub)

        if not aligned_list:
            return pd.DataFrame(
                columns=["event_time", "mean_log", "std_log", "n", "se", "ci_lower", "ci_upper"]
            )

        aligned_df = pd.concat(aligned_list, ignore_index=True)

        summary = (
            aligned_df.groupby("event_time")["log_best"]
            .agg(["mean", "std", "count"])
            .rename(columns={"mean": "mean_log", "std": "std_log", "count": "n"})
            .reset_index()
        )

        summary["se"] = summary["std_log"] / np.sqrt(summary["n"])
        summary["ci_lower"] = summary["mean_log"] - 1.96 * summary["se"]
        summary["ci_upper"] = summary["mean_log"] + 1.96 * summary["se"]

        summary = summary.sort_values("event_time").reset_index(drop=True)
        return summary

    summary_agree = align_and_summarize(valid_agreements)

    # --- plotting ---
    fig = plt.figure(figsize=figsize)
    sns.lineplot(data=summary_agree, x="event_time", y="mean_log", color="black", linewidth=2)
    plt.fill_between(
        summary_agree["event_time"],
        summary_agree["ci_lower"],
        summary_agree["ci_upper"],
        alpha=0.3,
        color="gray",
    )
    plt.axvline(0, color="#90353B", linestyle="--", label=treatment)
    plt.xlabel("months to treatment", fontsize=18)
    plt.ylabel("avg fatalities (log)", fontsize=18)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    # black spines
    plt.gca().spines["left"].set_color("black")
    plt.gca().spines["bottom"].set_color("black")
    # no grid lines
    plt.gca().grid(False)
    plt.margins(x=0)
    plt.legend(frameon=False, fontsize=18)

    plt.tick_params(axis="x", labelsize=18)
    plt.tick_params(axis="y", labelsize=18)
    # add tick marks on the x axis internally
    plt.gca().xaxis.set_ticks_position("bottom")
    plt.gca().yaxis.set_ticks_position("left")

    plt.tight_layout()
    if savepath:
        fig.savefig(savepath, bbox_inches="tight")
    plt.show()

    return {
        "agreement": (summary_agree, valid_agreements),
    }
