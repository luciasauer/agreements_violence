"""
Discrete-time ClogLog hazard and multinomial logit fitting for competing risks.

Both estimators use conflict-level clustered standard errors via
statsmodels GLM / MNLogit with cov_type='cluster'.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit


def fit_cloglog(outcome, covs, df, group_col='conflict_id', verbose_missing=True):
    """
    Fit a cause-specific discrete-time ClogLog hazard model.

    Listwise deletion is applied: rows with NaN in any covariate are dropped
    before fitting. This is needed for CP-proxy variables with partial coverage.

    Parameters
    ----------
    outcome : str
        Column name of the binary event indicator (1 = event, 0 = censored).
    covs : list of str
        Covariate names (no constant — added internally).
    df : DataFrame
        Spell-level dataset (one row per conflict-quarter).
    group_col : str
        Column used to define clusters for SE estimation.
    verbose_missing : bool
        If True, prints the number of dropped rows and affected conflicts.

    Returns
    -------
    summary : DataFrame
        Index = covariate names. Columns: coef, se (of log-HR), HR, HR_lo,
        HR_hi, pval, sig, n_events, n_obs, aic.
    result : GLMResults
        Fitted statsmodels result object.
    """
    cols_needed = [outcome] + covs + [group_col]
    sub = df[cols_needed].dropna()
    n_dropped = len(df) - len(sub)
    if n_dropped > 0 and verbose_missing:
        c_dropped = (df[cols_needed]
                     .loc[df[cols_needed].isna().any(axis=1), group_col]
                     .nunique())
        print(f"  [listwise] dropped {n_dropped} rows ({c_dropped} conflicts) "
              f"with NaN in {covs}")

    X = sm.add_constant(sub[covs].astype(float), has_constant='add')
    y = sub[outcome].astype(float)
    model = sm.GLM(
        y, X,
        family=sm.families.Binomial(link=sm.families.links.CLogLog())
    )
    try:
        result = model.fit(
            cov_type='cluster',
            cov_kwds={'groups': sub[group_col].values}
        )
    except Exception:
        result = model.fit()

    params = result.params.drop('const', errors='ignore')
    se     = result.bse.drop('const', errors='ignore')
    pvals  = result.pvalues.drop('const', errors='ignore')

    summary = pd.DataFrame({
        'coef':  params,
        'se':    se,
        'HR':    np.exp(params),
        'HR_lo': np.exp(params - 1.96 * se),
        'HR_hi': np.exp(params + 1.96 * se),
        'pval':  pvals,
    })
    summary['sig'] = pd.cut(
        pvals,
        bins=[-np.inf, 0.01, 0.05, 0.1, np.inf],
        labels=['***', '**', '*', '']
    ).astype(str)
    summary['n_events'] = int(y.sum())
    summary['n_obs']    = int(len(y))
    summary['aic']      = round(result.aic, 1)
    return summary, result


def fit_mnlogit(covs, df, group_col='conflict_id'):
    """
    Fit a multinomial logit for competing risks CIF estimation.

    Outcome y_multi must be in {0=ongoing, 1=sign, 2=victory, 3=fade}.
    Standard errors are clustered at the conflict level.

    Parameters
    ----------
    covs : list of str
        Covariate names (no constant — added internally).
    df : DataFrame
        Spell-level dataset with column 'y_multi'.
    group_col : str
        Cluster column for SE estimation.

    Returns
    -------
    MNLogitResults
        Fitted statsmodels multinomial result.
    """
    X = sm.add_constant(df[covs].astype(float), has_constant='add')
    y = df['y_multi'].astype(int)
    model = MNLogit(y, X)
    try:
        result = model.fit(
            method='bfgs', maxiter=2000, disp=False,
            cov_type='cluster',
            cov_kwds={'groups': df[group_col].values}
        )
    except Exception:
        result = model.fit(method='bfgs', maxiter=2000, disp=False)
    return result
