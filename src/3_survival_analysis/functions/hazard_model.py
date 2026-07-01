"""
hazard_utils.py
---------------
Discrete-time hazard model for time to first peace agreement.

Expected input: pre_treatment — the conflict-month panel already
restricted to pre-agreement observations (built in the notebook as):

    df_panel_capped = df_panel[
        (df_panel['year_mo'] >= df_panel['start_date']) &
        (df_panel['year_mo'] <= df_panel['end_date'])
    ]
    pre_treatment = df_panel_capped[
        (df_panel_capped['first_agreement_date'] == 0) |
        (df_panel_capped['year_mo_numeric'] <= df_panel_capped['first_agreement_date'])
    ].sort_values(['conflict_id', 'year_mo_numeric'])

Usage:
    from hazard_utils import prepare_spell, run_hazard, plot_km
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import scipy.stats as stats
from scipy.stats import norm as _norm
from patsy import dmatrix



# ─────────────────────────────────────────────────────────────────────────────
# RUN HAZARD MODEL
# ─────────────────────────────────────────────────────────────────────────────

def run_hazard(
    formula: str,
    spell: pd.DataFrame,
    label: str = "",
    cluster_var: str = "conflict_id",
) -> tuple:
    """
    Estimate a discrete-time cloglog hazard model (grouped Cox equivalent).

    exp(coef) = hazard ratio (HR):
      HR > 1 → variable increases the monthly probability of signing
      HR < 1 → variable decreases the monthly probability of signing

    Standard errors are clustered at the conflict level.

    Parameters
    ----------
    formula : str
        Patsy formula. Dependent variable must be is_first_agreement.
        Example:
            "is_first_agreement ~ log_conflict_age + log_cum_deaths
             + vdem_judicial_constraints_lag1y + C(region)"
    spell : pd.DataFrame
        Output of prepare_spell().
    label : str
        Header label for the printed table.
    cluster_var : str
        Column to cluster SEs on. Default: "conflict_id".

    Returns
    -------
    model : statsmodels GLMResultsWrapper
    table : pd.DataFrame  — HR, SE, CI_low, CI_high, z, p, sig
    """
    model = smf.glm(
        formula,
        data   = spell,
        family = sm.families.Binomial(sm.families.links.CLogLog()),
    ).fit(
        cov_type = "cluster",
        cov_kwds = {"groups": spell[cluster_var]},
    )

    ci = model.conf_int()

    def stars(p):
        if p < 0.001: return "***"
        if p < 0.01:  return "**"
        if p < 0.05:  return "*"
        if p < 0.10:  return "."
        return ""

    table = pd.DataFrame({
        "HR":     np.exp(model.params).round(3),
        "SE":     model.bse.round(3),
        "CI_low": np.exp(ci.iloc[:, 0]).round(3),
        "CI_high":np.exp(ci.iloc[:, 1]).round(3),
        "z":      model.tvalues.round(2),
        "p":      model.pvalues.round(3),
        "sig":    [stars(p) for p in model.pvalues],
    })

    print(f"\n{'═'*72}")
    if label:
        print(f"  {label}")
    print(f"  Formula : {formula}")
    print(f"  N = {int(model.nobs):,} | Events = {int(spell['is_first_agreement'].sum())} | AIC = {model.aic:.1f}")
    print(f"  Clustered SE at {cluster_var} level")
    print(f"{'─'*72}")
    print(f"  {'Variable':<40} {'HR':>7} {'SE':>7} {'CI_low':>8} {'CI_high':>8} {'z':>7} {'p':>7}  sig")
    print(f"{'─'*72}")

    for var, row in table.drop(index="Intercept", errors="ignore").iterrows():
        print(
            f"  {var:<40} {row['HR']:>7.3f} {row['SE']:>7.3f} "
            f"{row['CI_low']:>8.3f} {row['CI_high']:>8.3f} "
            f"{row['z']:>7.2f} {row['p']:>7.3f}  {row['sig']}"
        )

    print(f"{'─'*72}")
    print("  Signif. codes:  *** p<0.001  ** p<0.01  * p<0.05  . p<0.10")
    print("  HR > 1 = faster to agreement  |  HR < 1 = slower to agreement")
    print(f"{'═'*72}\n")

    return model, table



# ─────────────────────────────────────────────────────────────────────────────
# PREDICTED PROBABILITIES — delta-method CI
# ─────────────────────────────────────────────────────────────────────────────

def predict_cloglog_ci(model, col_dict, n, alpha=0.05):
    """
    Predicted quarterly hazard + delta-method 95% CI for a CLogLog GLM.

    Builds the design matrix in the exact column order of model.model.exog_names,
    propagates uncertainty through the non-linear link via the delta method,
    and returns predictions on the probability scale.

    Parameters
    ----------
    model    : fitted statsmodels GLMResultsWrapper (CLogLog family)
    col_dict : dict mapping each non-intercept exog_name → scalar or array of length n
    n        : number of prediction points (length of arrays in col_dict)
    alpha    : significance level for CI (default 0.05 → 95% CI)

    Returns
    -------
    pd.DataFrame with columns: prob, ci_lo, ci_hi
    """
    z          = _norm.ppf(1 - alpha / 2)
    exog_names = model.model.exog_names

    X = np.zeros((n, len(exog_names)), dtype=float)
    for j, name in enumerate(exog_names):
        if name in ('const', 'Intercept'):
            X[:, j] = 1.0
        elif name in col_dict:
            val     = col_dict[name]
            X[:, j] = val if hasattr(val, '__len__') else np.full(n, float(val))
        else:
            raise ValueError(
                f"'{name}' missing from col_dict.\n"
                f"Model expects : {exog_names}\n"
                f"You provided  : {list(col_dict.keys())}"
            )

    beta    = model.params.values.astype(float)
    cov     = model.cov_params().values.astype(float)
    eta     = X @ beta
    var_eta = np.einsum('ij,jk,ik->i', X, cov, X)
    se_eta  = np.sqrt(np.clip(var_eta, 0, None))

    inv = lambda v: 1.0 - np.exp(-np.exp(v))
    return pd.DataFrame({
        'prob' : inv(eta),
        'ci_lo': inv(eta - z * se_eta),
        'ci_hi': inv(eta + z * se_eta),
    })


def plot_hazard_two_panels(
    model_left,
    model_right,
    left_main,
    left_inter,
    right_main,
    right_inter,
    left_labels  = None,
    right_labels = None,
    left_title   = 'Left panel',
    right_title  = 'Right panel',
    age_max_left  = 24,
    age_max_right = 28,
    results_dir  = None,
    filename     = 'fig_predicted_hazard_combined.pdf',
):
    """
    Side-by-side predicted hazard panels from two CLogLog models.

    Each panel plots two lines (binary variable = 0 vs 1) with delta-method CI.
    The crossover quarter t* = exp(−β_main / β_inter) is annotated when it falls
    within the plotted range.

    Parameters
    ----------
    model_left / model_right : fitted CLogLog GLM
    left_main / right_main   : str — name of the binary main-effect parameter
    left_inter / right_inter : str — name of the age-interaction parameter
    left_labels / right_labels : dict {0: label, 1: label}
    left_title / right_title : str — panel titles
    age_max_left/right       : int — x-axis upper limit in quarters
    results_dir              : str or None — if given, saves PDF there
    filename                 : str — output filename
    """
    AGE_NAME = 'log_conflict_age_q'
    C_HIGH   = '#C0392B'
    C_LOW    = '#2471A3'
    pct_fmt  = mticker.FuncFormatter(lambda x, _: f'{x:.1f}%')

    if left_labels  is None: left_labels  = {0: 'Low',  1: 'High'}
    if right_labels is None: right_labels = {0: 'Low',  1: 'High'}

    def _panel(ax, model, main_name, inter_name, labels, age_max, title):
        age_grid     = np.linspace(1, age_max, 500)
        log_age_grid = np.log(age_grid)

        for val, color, lbl in [(0, C_LOW, labels[0]), (1, C_HIGH, labels[1])]:
            pred = predict_cloglog_ci(
                model,
                col_dict={
                    AGE_NAME   : log_age_grid,
                    main_name  : val,
                    inter_name : log_age_grid * val,
                },
                n=len(age_grid),
            )
            ax.plot(age_grid, pred['prob'] * 100, color=color, lw=2.2, label=lbl)
            ax.fill_between(age_grid,
                            pred['ci_lo'] * 100, pred['ci_hi'] * 100,
                            color=color, alpha=0.12)

        b_main  = model.params[main_name]
        b_inter = model.params[inter_name]
        if b_inter != 0:
            t_x = np.exp(-b_main / b_inter)
            if 1 < t_x <= age_max:
                ax.axvline(t_x, color='grey', lw=0.8, ls='--', alpha=0.6)
                ax.text(t_x + 0.3, 1.5,
                        f'Crossover\n($\\approx${t_x:.0f} qtrs)',
                        fontsize=10, color='grey', va='bottom')

        ticks = [q for q in [0, 4, 8, 12, 16, 20, 24, 28] if q <= age_max]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(q) for q in ticks])
        ax.set_xlim(0, age_max)
        ax.set_ylim(bottom=0)
        ax.set_xlabel('Conflict age (quarters)', fontsize=12)
        ax.tick_params(axis='both', labelsize=12)
        ax.yaxis.set_major_formatter(pct_fmt)
        ax.legend(frameon=False, fontsize=11, loc='upper right')
        ax.grid(axis='y', alpha=0.25, lw=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_title(title, fontsize=14, loc='left', pad=8)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    _panel(axes[0], model_left,  left_main,  left_inter,  left_labels,  age_max_left,  left_title)
    _panel(axes[1], model_right, right_main, right_inter, right_labels, age_max_right, right_title)
    axes[0].set_ylabel('Predicted quarterly hazard (%)', fontsize=12)

    plt.tight_layout()
    if results_dir:
        plt.savefig(f'{results_dir}{filename}', bbox_inches='tight')
    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# COX PROPORTIONAL HAZARDS — robustness check
# ─────────────────────────────────────────────────────────────────────────────

def run_cox(
    covariates: list,
    spell: pd.DataFrame,
    label: str = "",
    duration_col: str = "conflict_age_q",
    event_col: str    = "is_first_agreement",
    cluster_var: str  = "conflict_id",
) -> object:
    """
    Extended Cox PH model (lifelines CoxTimeVaryingFitter) using the quarterly spell
    in counting-process format. Supports time-varying covariates such as
    high_ia_bin:log_conflict_age_q — the Cox equivalent of the ClogLog interaction.

    The spell already has one row per conflict-quarter, so no collapse is needed.
    start = conflict_age_q - 1, stop = conflict_age_q per interval.

    Parameters
    ----------
    covariates   : list of str — column names (may include pre-built interaction columns)
    spell        : pd.DataFrame — quarterly spell (one row per conflict-quarter)
    label        : str — header for the printed table
    duration_col : str — quarterly period column in spell
    event_col    : str — event indicator column
    cluster_var  : str — conflict identifier (for cluster SEs)

    Returns
    -------
    cph : fitted CoxTimeVaryingFitter
    """
    from lifelines import CoxTimeVaryingFitter

    cols = [cluster_var, duration_col, event_col] + covariates
    df = spell[cols].dropna(subset=covariates).copy()

    # Counting-process format: (start, stop] interval per row
    df['_start'] = df[duration_col] - 1
    df['_stop']  = df[duration_col]

    cph = CoxTimeVaryingFitter()
    cph.fit(
        df,
        id_col       = cluster_var,
        start_col    = '_start',
        stop_col     = '_stop',
        event_col    = event_col,
        formula      = ' + '.join(covariates),
    )

    def stars(p):
        if p < 0.001: return "***"
        if p < 0.01:  return "**"
        if p < 0.05:  return "*"
        if p < 0.10:  return "."
        return ""

    n_obs    = int(df[cluster_var].nunique())
    n_events = int(df.groupby(cluster_var)[event_col].max().sum())

    print(f"\n{'═'*72}")
    if label:
        print(f"  {label}")
    print(f"  Extended Cox PH | N = {n_obs:,} conflicts | Events = {n_events}")
    print(f"  Clustered SE at {cluster_var} level")
    print(f"{'─'*72}")
    print(f"  {'Variable':<40} {'HR':>7} {'SE':>7} {'CI_low':>8} {'CI_high':>8} {'z':>7} {'p':>7}  sig")
    print(f"{'─'*72}")

    s = cph.summary
    for var in covariates:
        if var in s.index:
            hr    = np.exp(s.loc[var, 'coef'])
            se    = s.loc[var, 'se(coef)']
            ci_lo = np.exp(s.loc[var, 'coef lower 95%'])
            ci_hi = np.exp(s.loc[var, 'coef upper 95%'])
            z     = s.loc[var, 'z']
            p     = s.loc[var, 'p']
            print(
                f"  {var:<40} {hr:>7.3f} {se:>7.3f} "
                f"{ci_lo:>8.3f} {ci_hi:>8.3f} "
                f"{z:>7.2f} {p:>7.3f}  {stars(p)}"
            )

    print(f"{'─'*72}")
    print("  Signif. codes:  *** p<0.001  ** p<0.01  * p<0.05  . p<0.10")
    print("  HR > 1 = faster to agreement  |  HR < 1 = slower to agreement")
    print("  Non-parametric baseline; time-varying interaction terms allowed.")
    print(f"{'═'*72}\n")

    return cph

# ─────────────────────────────────────────────────────────────────────────────
# KAPLAN-MEIER
# ─────────────────────────────────────────────────────────────────────────────

def plot_km(
    spell: pd.DataFrame,
    group_col: str,
    group_labels: dict = None,
    colors: dict = None,
    title: str = "Kaplan-Meier: Time to First Agreement",
    max_months: int = 300,
):
    """
    Plot Kaplan-Meier survival curves by group.

    Collapses the spell to one row per conflict, then estimates S(t)
    = P(no agreement at time t) for each group. The log-rank test
    checks whether the curves are statistically different.

    Parameters
    ----------
    spell : pd.DataFrame
        Output of prepare_spell(). Must contain conflict_age,
        is_first_agreement, conflict_id, and group_col.
    group_col : str
        Column defining the groups (e.g. "high_commitment").
    group_labels : dict, optional  {value: label string}
    colors : dict, optional        {value: hex color}
    max_months : int               X-axis upper limit.
    """
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import multivariate_logrank_test

    # One row per conflict
    summary = (
        spell.groupby("conflict_id")
        .agg(
            duration = ("conflict_age", "max"),
            event    = ("is_first_agreement", "max"),
            group    = (group_col, "first"),
        )
        .reset_index()
        .dropna(subset=["group"])
    )

    groups = sorted(summary["group"].unique())
    default_colors = ["#2166AC", "#D6604D", "#4DAF4A", "#984EA3", "#FF7F00"]
    cmap   = colors or {g: default_colors[i % len(default_colors)]
                        for i, g in enumerate(groups)}
    lmap   = group_labels or {g: str(g) for g in groups}

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#F7F7F7")

    for g in groups:
        sub = summary[summary["group"] == g]
        kmf = KaplanMeierFitter(label=f"{lmap[g]} (n={len(sub)})")
        kmf.fit(sub["duration"], sub["event"])
        kmf.plot_survival_function(ax=ax, color=cmap.get(g, "grey"),
                                   lw=2.2, ci_show=True, ci_alpha=0.12)

    lr = multivariate_logrank_test(summary["duration"],
                                   summary["group"],
                                   summary["event"])

    ax.set_xlim(0, max_months)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Months since conflict start", fontsize=11)
    ax.set_ylabel("Pr(No agreement yet)", fontsize=11)
    ax.set_title(
        f"{title}\nLog-rank: χ² = {lr.test_statistic:.2f}, p = {lr.p_value:.3f}",
        fontsize=11, fontweight="bold",
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()

    print(f"Log-rank: χ² = {lr.test_statistic:.3f} | p = {lr.p_value:.4f}")