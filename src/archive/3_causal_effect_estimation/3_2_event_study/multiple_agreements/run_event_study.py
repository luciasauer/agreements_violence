import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
from diff_diff import CallawaySantAnna, plot_event_study


def run_event_study(
    df,
    outcome,
    unit,
    time,
    first_treat,
    controls=None,
    cluster=None,
    dyn=18,
    seed=1,
    subset=None,
    ytitle="ATT",
    xtitle="Event time",
    plot=True,
    quarterly=False
):
    """
    Replicates Stata csdid + estat event + estat cevent logic
    using diff-diff (CallawaySantAnna).
    """

    # ── Optional subsample ─────────────────────────────────────
    if subset is not None:
        df = df.query(subset).copy()

    # ── Prepare design matrix ───────────────────────────────────
    if controls is None:
        xvars = []
    else:
        xvars = controls

    cs = CallawaySantAnna(
        control_group="never_treated",
        estimation_method="dr",
        cluster=cluster,
        n_bootstrap=999,
        bootstrap_weights="rademacher",
        anticipation = 0,
        alpha=0.05,
        seed=seed
    )


    results = cs.fit(
        df,
        outcome=outcome,
        unit=unit,
        time=time,
        first_treat=first_treat,
        covariates=xvars,
        aggregate="event_study",
    )

    # ── Extract event study table ───────────────────────────────
    es = results.event_study_effects

    plot_df = pd.DataFrame([
        {
            "period": k,
            "effect": v["effect"],
            "se": v["se"],
        }
        for k, v in es.items()
    ]).sort_values("period")

    plot_df["ci_lb"] = plot_df["effect"] - 1.96 * plot_df["se"]
    plot_df["ci_ub"] = plot_df["effect"] + 1.96 * plot_df["se"]

    # ── estat cevent equivalent ─────────────────────────────────
    post_window = plot_df[(plot_df["period"] >= 1) & (plot_df["period"] <= dyn)]

    avg_effect = post_window["effect"].mean()
    avg_se = np.sqrt((post_window["se"] ** 2).mean())
    z_stat = avg_effect / avg_se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    ci_lb = avg_effect - 1.96 * avg_se
    ci_ub = avg_effect + 1.96 * avg_se

    results_table = pd.DataFrame({
        "Treated W":df.loc[df[first_treat] == dyn, unit].nunique(),
        "Control W":df.loc[df[first_treat] == 0, unit].nunique(),
        "Estimate": [round(avg_effect, 4)],
        "Std. Err.": [round(avg_se, 4)],
        "p-value": [round(p_value, 4)],
        "CI Lower": [round(ci_lb, 4)],
        "CI Upper": [round(ci_ub, 4)]
    })
    print('Average post-treatment effect (periods 1 to {}):'.format(dyn), "\n")
    print('=' * 80)
    print(results_table.to_string(index=False))
    print('=' * 80)
    # ── Plot (Stata-style rectangles) ──────────────────────────
    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))

        pre = plot_df[plot_df["period"] < 0]
        post = plot_df[plot_df["period"] >= 0]

        # Gridlines
        for x in [-dyn, -9, 0, 9, dyn]:
            ax.axvline(x, color="grey", linestyle="--", alpha=0.5, zorder=0)
        for y in [-2, -1, 1, 2]:
            ax.axhline(y, color="grey", linestyle="--", alpha=0.5, zorder=0)

        ax.axhline(0, color="black", linestyle="--")

        # CI rectangles
        ax.bar(pre["period"],
               pre["ci_ub"] - pre["ci_lb"],
               bottom=pre["ci_lb"],
               width=0.8,
               color="black",
               alpha=0.7)

        ax.bar(post["period"],
               post["ci_ub"] - post["ci_lb"],
               bottom=post["ci_lb"],
               width=0.8,
               color="#90353B",
               alpha=0.7)

        # Points
        ax.scatter(pre["period"], pre["effect"], color="black", s=25, zorder=3)
        ax.scatter(post["period"], post["effect"], color="#90353B", s=25, zorder=3)

        legend_elements = [
            mpatches.Patch(color="black", label="Pre-treatment"),
            mpatches.Patch(color="#90353B", label="Post-treatment"),
        ]

        ax.legend(handles=legend_elements, frameon=False, fontsize=16)

        ax.set_xlim(-dyn - 0.5, dyn + 0.5)
        ax.set_ylim(-2, 2)

        if quarterly:
            ax.set_xticks([-dyn, -3, 0, 3, dyn])
            ax.set_xticklabels([-dyn, -3, 0, 3, dyn], fontsize =16)
        else:

            ax.set_xticks([-dyn, -9, 0, 9, dyn])
            ax.set_xticklabels([-dyn, -9, 0, 9, dyn], fontsize =16)
        ax.set_yticks([-2, -1, 0, 1, 2])
        ax.set_yticklabels([-2, -1, 0, 1, 2], fontsize =16)

        ax.set_xlabel(xtitle, fontsize = 16)
        ax.set_ylabel(ytitle, fontsize = 16)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("black")
        ax.spines["bottom"].set_color("black")


        plt.tight_layout()
        plt.show()

    return plot_df