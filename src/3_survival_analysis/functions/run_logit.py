"""
logit_utils.py
--------------
Utility function to run logit regressions and return
a clean table with OR, SE, confidence intervals, and significance stars.

Usage:
    from logit_utils import run_logit

    model, table = run_logit(
        formula = "ever_agreement ~ commit_index + log_total_deaths + multiple_conflicts_binary",
        data    = conflict_level,
        label   = "H1: Commitment index",
    )
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def run_logit(
    formula: str,
    data: pd.DataFrame,
    label: str = "",
    drop_const: bool = True,
) -> tuple:
    """
    Run a logit regression and print a formatted results table.

    Parameters
    ----------
    formula : str
        Patsy formula string, e.g.:
        "ever_agreement ~ commit_index + log_total_deaths + C(region)"
    data : pd.DataFrame
        Dataset. Rows with any missing value in the formula variables
        are dropped automatically.
    label : str
        Label printed in the header of the output table.
    drop_const : bool
        Whether to drop the Intercept row from the printed table.
        Default: True.

    Returns
    -------
    model : statsmodels Logit result object
        Full statsmodels result, so you can access .predict(),
        .summary(), etc. afterwards.
    table : pd.DataFrame
        Formatted results table with columns:
        OR, SE, CI_low, CI_high, z, p, sig
    """
    model = smf.logit(formula, data=data).fit(disp=False)

    params = model.params
    se     = model.bse
    zstat  = model.tvalues
    pvals  = model.pvalues
    ci     = model.conf_int()

    def stars(p):
        if p < 0.001: return "***"
        if p < 0.01:  return "**"
        if p < 0.05:  return "*"
        if p < 0.10:  return "."
        return ""

    table = pd.DataFrame({
        "OR":     np.exp(params).round(3),
        "SE":     se.round(3),
        "CI_low": np.exp(ci.iloc[:, 0]).round(3),
        "CI_high":np.exp(ci.iloc[:, 1]).round(3),
        "z":      zstat.round(2),
        "p":      pvals.round(3),
        "sig":    [stars(p) for p in pvals],
    })

    if drop_const and "Intercept" in table.index:
        table_print = table.drop("Intercept")
    else:
        table_print = table

    # ── Header ───────────────────────────────────────────────────────────────
    n_obs    = int(model.nobs)
    r2       = model.prsquared
    ll       = model.llf
    llr_p    = model.llr_pvalue
    n_events = int(data[formula.split("~")[0].strip()].dropna().sum())

    print(f"\n{'═'*72}")
    if label:
        print(f"  {label}")
    print(f"  Formula : {formula}")
    print(f"  N = {n_obs} | Events = {n_events} | McFadden R² = {r2:.3f}")
    print(f"  Log-likelihood = {ll:.1f} | LLR p-value = {llr_p:.4f}")
    print(f"{'─'*72}")
    print(f"  {'Variable':<35} {'OR':>7} {'SE':>7} {'CI_low':>8} {'CI_high':>8} {'z':>7} {'p':>7}  sig")
    print(f"{'─'*72}")

    for var, row in table_print.iterrows():
        print(
            f"  {var:<35} "
            f"{row['OR']:>7.3f} "
            f"{row['SE']:>7.3f} "
            f"{row['CI_low']:>8.3f} "
            f"{row['CI_high']:>8.3f} "
            f"{row['z']:>7.2f} "
            f"{row['p']:>7.3f}  "
            f"{row['sig']}"
        )

    print(f"{'─'*72}")
    print("  Signif. codes:  *** p<0.001  ** p<0.01  * p<0.05  . p<0.10")
    print(f"{'═'*72}\n")

    return model, table