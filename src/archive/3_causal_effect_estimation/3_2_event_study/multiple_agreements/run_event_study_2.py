import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
from diff_diff import CallawaySantAnna


# ---------------------------
# Helpers
# ---------------------------

def _build_event_study_df(results, alpha=0.05):
    """
    Turn results.event_study_effects into a tidy DataFrame.
    Uses normal approx CI (like many event-study plots).
    """
    es = results.event_study_effects  # {period: {"effect":..., "se":...}, ...}
    plot_df = (
        pd.DataFrame(
            [{"period": k, "effect": v["effect"], "se": v["se"]} for k, v in es.items()]
        )
        .sort_values("period")
        .reset_index(drop=True)
    )

    zcrit = stats.norm.ppf(1 - alpha / 2)
    plot_df["ci_lb"] = plot_df["effect"] - zcrit * plot_df["se"]
    plot_df["ci_ub"] = plot_df["effect"] + zcrit * plot_df["se"]
    return plot_df


def csdid_like_cevent(
    df,
    results,
    first_treat_col,
    unit_col,
    cluster_col=None,
    start=1,
    end=18,
    alpha=0.05,
):
    """
    Stata-like `estat cevent, window(start end)`:
    average of ATT(e) for e in [start, end] + correct SE using influence functions.

    Requires:
      - aggregate="event_study" in cs.fit(...)
      - results.influence_functions available
    """

    es = results.event_study_effects
    periods = np.array(sorted(es.keys()))
    effects = np.array([es[p]["effect"] for p in periods])

    mask = (periods >= start) & (periods <= end)
    if mask.sum() == 0:
        raise ValueError(f"No periods found in [{start},{end}] in event_study_effects.")

    # point estimate: simple average over window
    avg_effect = effects[mask].mean()
    m = int(mask.sum())

    # Influence functions for correct SE
    IF = results.influence_functions
    if IF is None:
        raise ValueError(
            "results.influence_functions is None. "
            "Check your diff-diff version / estimation settings."
        )

    # Align IF columns to the event-study periods
    k = len(periods)
    if IF.shape[1] == k:
        IF_es = IF
    elif IF.shape[1] == k + 1:
        # common pattern: first col is 'overall', rest are event times
        IF_es = IF[:, 1:]
    else:
        raise ValueError(
            f"Cannot align influence_functions: IF.shape={IF.shape}, "
            f"#event-study periods={k}."
        )

    # linear combo: average of selected event times
    w = np.ones(m) / m
    IF_theta = IF_es[:, mask] @ w  # (n,)

    n = IF_theta.shape[0]

    if cluster_col is None:
        var_theta = np.sum(IF_theta**2) / (n**2)
    else:
        cl = df[cluster_col].to_numpy()
        tmp = pd.DataFrame({"cluster": cl, "if": IF_theta})
        IF_c = tmp.groupby("cluster", sort=False)["if"].sum().to_numpy()
        var_theta = np.sum(IF_c**2) / (n**2)

    avg_se = float(np.sqrt(var_theta))

    # inference
    z = avg_effect / avg_se if avg_se > 0 else np.nan
    p_value = 2 * (1 - stats.norm.cdf(abs(z))) if np.isfinite(z) else np.nan
    zcrit = stats.norm.ppf(1 - alpha / 2)
    ci_lb = avg_effect - zcrit * avg_se
    ci_ub = avg_effect + zcrit * avg_se

    # treated/control counts (stata-like idea)
    treated_units = df.loc[df[first_treat_col] > 0, unit_col].nunique()
    control_units = df.loc[df[first_treat_col] == 0, unit_col].nunique()

    return pd.DataFrame(
        {
            "Treated units": [treated_units],
            "Control units": [control_units],
            "Window": [f"{start}..{end}"],
            "Estimate": [avg_effect],
            "Std. Err.": [avg_se],
            "z": [z],
            "p-value": [p_value],
            "CI Lower": [ci_lb],
            "CI Upper": [ci_ub],
        }
    )


# ---------------------------
# Core estimation
# ---------------------------

def estimate_event_study(
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
    alpha=0.05,
    print_cevent=True,
):
    """
    Estimate event-study via CallawaySantAnna, and compute Stata-like cevent(1..dyn).

    Returns:
      plot_df, cevent_table, results
    """

    df_est = df.query(subset).copy() if subset is not None else df.copy()
    xvars = [] if controls is None else controls

    cs = CallawaySantAnna(
        control_group="never_treated",
        estimation_method="dr",
        cluster=cluster,
        n_bootstrap=999,
        bootstrap_weights="rademacher",
        anticipation=0,
        alpha=alpha,
        seed=seed,
    )

    results = cs.fit(
        df_est,
        outcome=outcome,
        unit=unit,
        time=time,
        first_treat=first_treat,
        covariates=xvars,
        aggregate="event_study",
    )

    plot_df = _build_event_study_df(results, alpha=alpha)

    cevent_table = csdid_like_cevent(
        df=df_est,
        results=results,
        first_treat_col=first_treat,
        unit_col=unit,
        cluster_col=cluster,
        start=1,
        end=dyn,
        alpha=alpha,
    )

    if print_cevent:
        print(f"\nCevent-style average post-treatment effect (periods 1 to {dyn}):\n")
        print("=" * 80)
        print(cevent_table.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
        print("=" * 80)

    return plot_df, cevent_table, results


# ---------------------------
# Plotting
# ---------------------------

def plot_event_study_axis(
    plot_df,
    ax,
    dyn=18,
    title=None,
    ytitle=None,
    xtitle=None,
    show_legend=False,
    ylims=None,   # optional: (ymin, ymax)
):
    pre = plot_df[plot_df["period"] < 0]
    post = plot_df[plot_df["period"] >= 0]

    # vertical grid
    for x in [-dyn, -dyn / 2, 0, dyn / 2, dyn]:
        ax.axvline(x, color="grey", linestyle="--", alpha=0.5, zorder=0)

    ax.axhline(0, color="black", linestyle="--")

    # CI bars
    ax.bar(
        pre["period"],
        pre["ci_ub"] - pre["ci_lb"],
        bottom=pre["ci_lb"],
        width=0.8,
        color="black",
        alpha=0.7,
    )

    ax.bar(
        post["period"],
        post["ci_ub"] - post["ci_lb"],
        bottom=post["ci_lb"],
        width=0.8,
        color="#90353B",
        alpha=0.7,
    )

    # points
    ax.scatter(pre["period"], pre["effect"], color="black", s=25, zorder=3)
    ax.scatter(post["period"], post["effect"], color="#90353B", s=25, zorder=3)

    ax.set_xlim(-dyn - 0.5, dyn + 0.5)

    # y-lims: either user-given or auto from CI range
    if ylims is None:
        ymin = float(plot_df["ci_lb"].min())
        ymax = float(plot_df["ci_ub"].max())
        pad = 0.10 * (ymax - ymin) if ymax > ymin else 0.5
        ylims = (ymin - pad, ymax + pad)
    ax.set_ylim(*ylims)

    xticks = [-dyn, int(round(-dyn / 2)), 0, int(round(dyn / 2)), dyn]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticks, fontsize=16)

    if title:
        ax.set_title(title, fontsize=16)
    if ytitle:
        ax.set_ylabel(ytitle, fontsize=16)
    if xtitle:
        ax.set_xlabel(xtitle, fontsize=16)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if show_legend:
        legend_elements = [
            mpatches.Patch(color="black", label="Pre-treatment"),
            mpatches.Patch(color="#90353B", label="Post-treatment"),
        ]
        ax.legend(handles=legend_elements, frameon=False, fontsize=16)


def run_event_study_panels(
    df,
    subsets,
    titles,
    nrows,
    ncols,
    outcome,
    unit,
    time,
    first_treat,
    controls=None,
    cluster=None,
    dyn=18,
    seed=1,
    alpha=0.05,
    ytitle="ATT",
    xtitle="Event time",
    print_cevent=False,
):
    """
    Runs event studies for multiple subsets and plots them in panels.

    If print_cevent=True, prints the IF-based cevent(1..dyn) for each panel.
    """

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(5 * ncols, 4 * nrows),
        sharex=True,
        sharey=True,
    )
    axes = np.array(axes).reshape(-1)

    # compute global y-lims across all panels for comparability
    all_plot_dfs = []
    all_cevents = []

    for subset in subsets:
        plot_df, cevent_table, _ = estimate_event_study(
            df=df,
            outcome=outcome,
            unit=unit,
            time=time,
            first_treat=first_treat,
            controls=controls,
            cluster=cluster,
            dyn=dyn,
            seed=seed,
            subset=subset,
            alpha=alpha,
            print_cevent=False,
        )
        all_plot_dfs.append(plot_df)
        all_cevents.append(cevent_table)

    global_lb = min(d["ci_lb"].min() for d in all_plot_dfs)
    global_ub = max(d["ci_ub"].max() for d in all_plot_dfs)
    pad = 0.10 * (global_ub - global_lb) if global_ub > global_lb else 0.5
    global_ylims = (float(global_lb - pad), float(global_ub + pad))

    for i, (plot_df, cevent_table) in enumerate(zip(all_plot_dfs, all_cevents)):
        plot_event_study_axis(
            plot_df,
            ax=axes[i],
            dyn=dyn,
            title=titles[i],
            ytitle=ytitle if i % ncols == 0 else None,
            xtitle=xtitle if i >= (nrows - 1) * ncols else None,
            show_legend=(i == 0),
            ylims=global_ylims,
        )

        if print_cevent:
            print("\n" + "=" * 80)
            print(f"{titles[i]} — Cevent average (periods 1..{dyn})")
            print("=" * 80)
            print(cevent_table.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
            print("=" * 80)

    plt.tight_layout()
    plt.show()