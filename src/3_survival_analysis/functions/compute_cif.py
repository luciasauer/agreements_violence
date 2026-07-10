"""
Cumulative Incidence Function (CIF) for competing risks.

Framework
---------
Three mutually exclusive exits: signing (S), military victory (V), conflict fade (F).

    S(t) = prod_{u=1}^{t} [1 - h_S(u) - h_V(u) - h_F(u)],   S(0) = 1
    CIF_k(T) = sum_{t=1}^{T} h_k(t) * S(t-1)

Sub-hazards h_k come from a MNLogit (outcome 0=none, 1=sign, 2=victory, 3=fade),
which guarantees sum_k h_k ≤ 1 by construction.

Public API
----------
make_profile(covs, age_range, **kwargs)
    Build design matrix for a fixed covariate profile.

compute_cif(mn_result, covs, age_range, **profile)
    CIF at a single fixed profile.

compute_cif_gformula(mn_result, covs, age_range, spell_df,
                     conflict_id_col, intervention)
    G-formula (standardized) CIF: for each conflict use their actual covariates
    with the intervention applied, then average across conflicts.

bootstrap_cif(mn_result, X, y, conflict_ids, covs, age_range,
              method, profile, intervention, spell_df, ...)
    Cluster bootstrap (resample whole conflicts) returning point estimate,
    SE, and 95 % percentile CI for both methods.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from collections import defaultdict


# ── Constants ─────────────────────────────────────────────────────────────────

_BIN_NAMES = ['abin_5_8Q', 'abin_9_16Q', 'abin_17_32Q', 'abin_33pQ']

# Covariates that are purely functions of conflict age (never static per conflict)
_AGE_COLS = frozenset({'log_conflict_age_q', *_BIN_NAMES})


# ── Internal helpers ──────────────────────────────────────────────────────────

def _bin_values(t):
    """Age-bin dummy dict for quarter t (right-inclusive: 1–4, 5–8, 9–16, 17–32, 33+)."""
    row = {b: 0.0 for b in _BIN_NAMES}
    if   5 <= t <= 8:   row['abin_5_8Q']   = 1.0
    elif 9 <= t <= 16:  row['abin_9_16Q']  = 1.0
    elif 17 <= t <= 32: row['abin_17_32Q'] = 1.0
    elif t >= 33:       row['abin_33pQ']   = 1.0
    return row


def _get_static_covs(covs):
    """Covariate names that are static per conflict (not age-derived, not interactions)."""
    return [c for c in covs if c not in _AGE_COLS and '_x_' not in c]


def _gformula_average(mn_result, covs, age_range, static_rows, intervention):
    """
    Average CIF over a list of per-conflict static-covariate dicts.

    For each dict, apply the intervention override, compute CIF, then average.
    Used internally by compute_cif_gformula and bootstrap_cif.
    """
    age_range = np.asarray(age_range)
    T         = len(age_range)
    sum_S     = np.zeros(T)
    sum_V     = np.zeros(T)
    sum_F     = np.zeros(T)

    for kwargs in static_rows:
        kw    = {**kwargs, **intervention}   # intervention overrides actual values
        cif_i = compute_cif(mn_result, covs, age_range, **kw)
        sum_S += cif_i['CIF_S'].values
        sum_V += cif_i['CIF_V'].values
        sum_F += cif_i['CIF_F'].values

    n = len(static_rows)
    return pd.DataFrame({
        'age_q': age_range,
        'CIF_S': sum_S / n,
        'CIF_V': sum_V / n,
        'CIF_F': sum_F / n,
    })


# ── Public: profile builder ───────────────────────────────────────────────────

def make_profile(covs, age_range, **kwargs):
    """
    Build a prediction matrix for a fixed covariate profile over conflict ages.

    Time-varying columns (log_conflict_age_q, abin_*) are computed from age_range.
    All other kwargs are treated as static per conflict.

    Interaction terms are resolved generically for any kwarg variable:
      - log_age_x_{var}   if present in covs
      - {bin}_x_{var}     if present in covs
    Legacy IA/EF aliases (_x_ia, _x_ef) are also handled.

    Parameters
    ----------
    covs : list of str
        Covariate names from the fitted model (without constant).
    age_range : array-like
        Conflict-age quarters (e.g. np.arange(1, 41)).
    **kwargs
        Profile values. Unrecognised variables pass through as static.
        Example: high_ia_bin=1, d_2010s=1, loot_onset=0.

    Returns
    -------
    ndarray (T, len(covs)+1) — design matrix with constant prepended.
    """
    ia_bin = kwargs.get('high_ia_bin', 0)
    ef_bin = kwargs.get('high_fe_etfra_bin', 0)

    rows = []
    for t in age_range:
        log_age = np.log1p(t)
        bins    = _bin_values(t)

        # Start with all static kwargs, then override with time-varying values
        row = dict(kwargs)
        row['log_conflict_age_q'] = log_age
        row.update(bins)

        # Legacy IA / EF interaction naming (_x_ia, _x_ef)
        row['log_age_x_ia'] = log_age * ia_bin
        row['log_age_x_ef'] = log_age * ef_bin
        for b in _BIN_NAMES:
            row[f'{b}_x_ia'] = bins[b] * ia_bin
            row[f'{b}_x_ef'] = bins[b] * ef_bin

        # Generic interactions for any other kwarg variable that appears in covs
        for var, val in kwargs.items():
            if var in {'high_ia_bin', 'high_fe_etfra_bin'}:
                continue                        # already handled via legacy aliases
            lag_key = f'log_age_x_{var}'
            if lag_key in covs and lag_key not in row:
                row[lag_key] = log_age * val
            for b in _BIN_NAMES:
                bin_key = f'{b}_x_{var}'
                if bin_key in covs and bin_key not in row:
                    row[bin_key] = bins[b] * val

        rows.append(row)

    df_pred = pd.DataFrame(rows)
    avail   = [c for c in covs if c in df_pred.columns]
    missing = set(covs) - set(avail)
    if missing:
        print(f'  WARNING make_profile: missing columns = {missing}')

    return sm.add_constant(df_pred[avail].astype(float), has_constant='add')


# ── Public: fixed-profile CIF ─────────────────────────────────────────────────

def compute_cif(mn_result, covs, age_range, **profile):
    """
    Compute CIF from a fitted MNLogit at a single fixed covariate profile.

    Parameters
    ----------
    mn_result : MNLogitResults
    covs : list of str
    age_range : array-like
    **profile : covariate values (passed to make_profile)

    Returns
    -------
    DataFrame: age_q, h_S, h_V, h_F, S, CIF_S, CIF_V, CIF_F
    """
    X_pred = make_profile(covs, age_range, **profile)
    probs  = mn_result.predict(X_pred).values   # (T, 4): none / sign / victory / fade
    h_S, h_V, h_F = probs[:, 1], probs[:, 2], probs[:, 3]

    T     = len(age_range)
    S     = np.zeros(T)
    CIF_S = np.zeros(T)
    CIF_V = np.zeros(T)
    CIF_F = np.zeros(T)

    for i in range(T):
        S_prev   = 1.0 if i == 0 else S[i - 1]
        CIF_S[i] = (0.0 if i == 0 else CIF_S[i - 1]) + h_S[i] * S_prev
        CIF_V[i] = (0.0 if i == 0 else CIF_V[i - 1]) + h_V[i] * S_prev
        CIF_F[i] = (0.0 if i == 0 else CIF_F[i - 1]) + h_F[i] * S_prev
        S[i]     = S_prev * (1.0 - h_S[i] - h_V[i] - h_F[i])

    return pd.DataFrame({
        'age_q': age_range,
        'h_S': h_S, 'h_V': h_V, 'h_F': h_F,
        'S': S,
        'CIF_S': CIF_S, 'CIF_V': CIF_V, 'CIF_F': CIF_F,
    })


# ── Public: g-formula CIF ─────────────────────────────────────────────────────

def compute_cif_gformula(mn_result, covs, age_range, spell_df,
                          conflict_id_col, intervention):
    """
    G-formula (standardized) CIF.

    For each conflict, take their actual static covariates, apply the
    intervention, compute their individual CIF, then average across conflicts.

    Answers: "If we set {intervention} for all conflicts in the sample, what
    would the average CIF be?" — marginalizing over the actual covariate
    distribution rather than evaluating at a hypothetical reference point.

    Parameters
    ----------
    mn_result : MNLogitResults
    covs : list of str
    age_range : array-like
    spell_df : DataFrame
        Full spell panel (or conflict-level). Must contain conflict_id_col
        and all static covariates (inferred from covs via _get_static_covs).
    conflict_id_col : str
    intervention : dict
        Variables to override for every conflict, e.g. {'high_ia_bin': 1}.

    Returns
    -------
    DataFrame: age_q, CIF_S, CIF_V, CIF_F  (averaged over conflicts)
    """
    static_cols = _get_static_covs(covs)
    conflict_df = spell_df.groupby(conflict_id_col)[static_cols].first()

    static_dict = {
        cid: {c: float(conflict_df.loc[cid, c]) for c in static_cols}
        for cid in conflict_df.index
    }
    return _gformula_average(mn_result, covs, np.asarray(age_range),
                              list(static_dict.values()), intervention)


# ── Public: cluster-bootstrapped CIF ─────────────────────────────────────────

def bootstrap_cif(mn_result, X, y, conflict_ids, covs, age_range,
                  method='fixed',
                  profile=None,
                  intervention=None,
                  spell_df=None,
                  conflict_id_col='conflict_id',
                  n_boot=200,
                  seed=42,
                  horizons=None,
                  verbose=True):
    """
    Cluster-bootstrapped CIF with SE and 95 % percentile CI.

    Resamples whole conflicts with replacement, re-fits MNLogit on each
    bootstrap sample, re-computes CIF.  SE = std(bootstrap draws).

    Parameters
    ----------
    mn_result : MNLogitResults
        Fitted on the original sample; used for the point estimate only.
    X : ndarray (N, k+1)
        Design matrix with constant (as passed to MNLogit).
    y : array-like (N,)
        Multinomial outcome: 0=none, 1=sign, 2=victory, 3=fade.
    conflict_ids : array-like (N,)
        Conflict identifier per row; defines the resampling clusters.
    covs : list of str
        Covariate names (without constant).
    age_range : array-like
    method : {'fixed', 'gformula'}
        'fixed'    — evaluate CIF at a single profile (profile kwarg).
        'gformula' — average over sample with intervention applied.
    profile : dict, optional
        Required for method='fixed'. Covariate values for evaluation.
    intervention : dict, optional
        Required for method='gformula'. Variables to override per conflict.
    spell_df : DataFrame, optional
        Required for method='gformula'. Contains conflict_id_col and covariates.
    conflict_id_col : str
    n_boot : int
    seed : int
    horizons : list of int, optional
        Specific quarters at which to report SE/CI (e.g. [4, 8, 20, 40]).
    verbose : bool

    Returns
    -------
    dict with:
        'point'      DataFrame  — original-sample CIF (compute_cif / gformula)
        'curves'     DataFrame  — per-quarter mean, SE, CI for CIF_S/V/F
        'horizons'   DataFrame  — horizon-specific table (only if horizons given)
        'boot_draws' ndarray    — (n_valid, T, 3) raw bootstrap CIF_S/V/F draws
        'n_valid'    int        — number of successful bootstrap iterations
        'n_boot'     int
        'method'     str

    Usage
    -----
    # Fixed profile:
    boot = bootstrap_cif(mn_result, X, y, spell_q['conflict_id'], covs, AGE_RANGE,
                         method='fixed', profile={'high_ia_bin': 1},
                         n_boot=200, horizons=[4, 8, 20, 40])
    curves = boot['curves']
    ax.plot(curves['age_q'], curves['CIF_S_mean'])
    ax.fill_between(curves['age_q'], curves['CIF_S_lo'], curves['CIF_S_hi'], alpha=.2)

    # G-formula:
    boot_gf = bootstrap_cif(mn_result, X, y, spell_q['conflict_id'], covs, AGE_RANGE,
                             method='gformula', intervention={'high_ia_bin': 1},
                             spell_df=spell_q, conflict_id_col='conflict_id',
                             n_boot=200, horizons=[4, 8, 20, 40])
    """
    if method not in ('fixed', 'gformula'):
        raise ValueError(f"method must be 'fixed' or 'gformula', got {method!r}")
    if method == 'fixed' and profile is None:
        raise ValueError("method='fixed' requires a profile dict")
    if method == 'gformula' and (intervention is None or spell_df is None):
        raise ValueError("method='gformula' requires intervention and spell_df")

    age_range    = np.asarray(age_range)
    conflict_ids = np.asarray(conflict_ids)
    y            = np.asarray(y)
    T            = len(age_range)

    # ── Point estimate on original sample ────────────────────────────────────
    if method == 'fixed':
        point = compute_cif(mn_result, covs, age_range, **profile)
    else:
        point = compute_cif_gformula(
            mn_result, covs, age_range, spell_df, conflict_id_col, intervention
        )

    # ── Cluster index: conflict_id → list of row positions ───────────────────
    unique_ids  = np.unique(conflict_ids)
    n_conflicts = len(unique_ids)
    id_to_rows  = defaultdict(list)
    for i, cid in enumerate(conflict_ids):
        id_to_rows[cid].append(i)

    # ── Pre-build static-covariate lookup for g-formula ──────────────────────
    if method == 'gformula':
        static_cols = _get_static_covs(covs)
        conf_df     = spell_df.groupby(conflict_id_col)[static_cols].first()
        static_dict = {
            cid: {c: float(conf_df.loc[cid, c]) for c in static_cols}
            for cid in conf_df.index
        }

    # ── Bootstrap loop ────────────────────────────────────────────────────────
    rng        = np.random.default_rng(seed)
    boot_draws = np.full((n_boot, T, 3), np.nan)   # axis-2: S / V / F
    n_failed   = 0

    for b in range(n_boot):
        if verbose and (b + 1) % 50 == 0:
            print(f'  Bootstrap {b + 1}/{n_boot}  (failed: {n_failed})',
                  end='\r', flush=True)

        # Resample conflicts (counting duplicates)
        boot_sample = rng.choice(unique_ids, size=n_conflicts, replace=True)
        boot_rows   = np.concatenate([id_to_rows[cid] for cid in boot_sample])
        X_b = X[boot_rows]
        y_b = y[boot_rows]

        try:
            mn_b = sm.MNLogit(y_b, X_b).fit(
                method='newton', maxiter=200, disp=0, warn_convergence=False,
            )
        except Exception:
            n_failed += 1
            continue

        try:
            if method == 'fixed':
                cif_b = compute_cif(mn_b, covs, age_range, **profile)
            else:
                # Use bootstrapped set of conflicts (with repetitions for averaging)
                boot_static = [static_dict[cid] for cid in boot_sample
                               if cid in static_dict]
                cif_b = _gformula_average(mn_b, covs, age_range,
                                           boot_static, intervention)

            boot_draws[b, :, 0] = cif_b['CIF_S'].values
            boot_draws[b, :, 1] = cif_b['CIF_V'].values
            boot_draws[b, :, 2] = cif_b['CIF_F'].values
        except Exception:
            n_failed += 1

    if verbose:
        print(f'\n  Bootstrap done: {n_boot - n_failed}/{n_boot} converged.')

    # ── Summarise bootstrap distribution ─────────────────────────────────────
    valid      = ~np.isnan(boot_draws[:, 0, 0])
    boot_valid = boot_draws[valid]
    n_valid    = int(valid.sum())

    def _summ(k):
        d = boot_valid[:, :, k]
        return dict(mean=np.mean(d, 0), se=np.std(d, 0, ddof=1),
                    lo=np.percentile(d, 2.5, 0), hi=np.percentile(d, 97.5, 0))

    ss, sv, sf = _summ(0), _summ(1), _summ(2)

    curves = pd.DataFrame({
        'age_q':      age_range,
        'CIF_S_mean': ss['mean'], 'CIF_S_se': ss['se'],
        'CIF_S_lo':   ss['lo'],   'CIF_S_hi': ss['hi'],
        'CIF_V_mean': sv['mean'], 'CIF_V_se': sv['se'],
        'CIF_V_lo':   sv['lo'],   'CIF_V_hi': sv['hi'],
        'CIF_F_mean': sf['mean'], 'CIF_F_se': sf['se'],
        'CIF_F_lo':   sf['lo'],   'CIF_F_hi': sf['hi'],
    })

    result = dict(point=point, curves=curves,
                  boot_draws=boot_valid, n_valid=n_valid,
                  n_boot=n_boot, method=method)

    if horizons is not None:
        h_rows = []
        for h in horizons:
            idx = min(int(np.searchsorted(age_range, h)), T - 1)
            row = {'horizon': h, 'age_q': int(age_range[idx])}
            for name, k in [('S', 0), ('V', 1), ('F', 2)]:
                d = boot_valid[:, idx, k]
                row[f'CIF_{name}_mean'] = np.mean(d)
                row[f'CIF_{name}_se']   = np.std(d, ddof=1)
                row[f'CIF_{name}_lo']   = np.percentile(d, 2.5)
                row[f'CIF_{name}_hi']   = np.percentile(d, 97.5)
            h_rows.append(row)
        result['horizons'] = pd.DataFrame(h_rows)

    return result
