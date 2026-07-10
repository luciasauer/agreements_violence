"""
LaTeX table generation for ClogLog hazard ratio results.

The main export function is build_latex_table. Variable label
dictionaries and column headers for the three baseline types
(log-age, age-bins, age-bins + decade controls) are also exported.
"""

# ── Variable label dictionaries ───────────────────────────────────────────────

VAR_LATEX_LOG = {
    'log_conflict_age_q':  r'$\log(\text{Age})$',
    'high_ia_bin':         r'$\text{HighIA}$',
    'log_age_x_ia':        r'$\log(\text{Age})\times\text{HighIA}$',
    'high_fe_etfra_bin':   r'$\text{HighEF}$',
    'log_age_x_ef':        r'$\log(\text{Age})\times\text{HighEF}$',
}

VAR_LATEX_BINS = {
    'abin_5_8Q':          r'$\mathbf{1}[\text{5--8Q}]$',
    'abin_9_16Q':         r'$\mathbf{1}[\text{9--16Q}]$',
    'abin_17_32Q':        r'$\mathbf{1}[\text{17--32Q}]$',
    'abin_33pQ':          r'$\mathbf{1}[\geq\text{33Q}]$',
    'high_ia_bin':        r'$\text{HighIA}$',
    'abin_5_8Q_x_ia':     r'$\mathbf{1}[\text{5--8Q}]\times\text{HighIA}$',
    'abin_9_16Q_x_ia':    r'$\mathbf{1}[\text{9--16Q}]\times\text{HighIA}$',
    'abin_17_32Q_x_ia':   r'$\mathbf{1}[\text{17--32Q}]\times\text{HighIA}$',
    'abin_33pQ_x_ia':     r'$\mathbf{1}[\geq\text{33Q}]\times\text{HighIA}$',
    'high_fe_etfra_bin':  r'$\text{HighEF}$',
    'abin_5_8Q_x_ef':     r'$\mathbf{1}[\text{5--8Q}]\times\text{HighEF}$',
    'abin_9_16Q_x_ef':    r'$\mathbf{1}[\text{9--16Q}]\times\text{HighEF}$',
    'abin_17_32Q_x_ef':   r'$\mathbf{1}[\text{17--32Q}]\times\text{HighEF}$',
    'abin_33pQ_x_ef':     r'$\mathbf{1}[\geq\text{33Q}]\times\text{HighEF}$',
}

VAR_LATEX_BINS_DEC = dict(VAR_LATEX_BINS)
VAR_LATEX_BINS_DEC.update({
    'd_2000s': r'$\mathbf{1}[\geq 2000]$',
    'd_2010s': r'$\mathbf{1}[\geq 2010]$',
    'd_2020s': r'$\mathbf{1}[\geq 2020]$',
})

# ── Column header dictionaries ────────────────────────────────────────────────

COL_HDR_LOG = {
    'M1': ('(M1)', 'Baseline'),
    'M2': ('(M2)', 'IA add.'),
    'M3': ('(M3)', r'IA$\times$age'),
    'M4': ('(M4)', 'EF add.'),
    'M5': ('(M5)', r'EF$\times$age'),
    'M6': ('(M6)', 'Combined'),
}

COL_HDR_BINS = {
    'M1b': ('(M1)', 'Baseline'),
    'M2b': ('(M2)', 'IA add.'),
    'M3b': ('(M3)', r'IA$\times$bins'),
    'M4b': ('(M4)', 'EF add.'),
    'M5b': ('(M5)', r'EF$\times$bins'),
    'M6b': ('(M6)', 'Combined'),
}

COL_HDR_BINS_DEC = {
    'M1c': ('(M1)', 'Baseline'),
    'M2c': ('(M2)', 'IA add.'),
    'M3c': ('(M3)', r'IA$\times$bins'),
    'M4c': ('(M4)', 'EF add.'),
    'M5c': ('(M5)', r'EF$\times$bins'),
    'M6c': ('(M6)', 'Combined'),
}

# ── Default notes template ────────────────────────────────────────────────────

NOTES_CLOGLOG = (
    r'\textit{{Notes:}} Hazard ratios from a discrete-time ClogLog GLM '
    r'({censor_note}). {hr_note} '
    r'$\text{{HighIA}}=1$ if \texttt{{experience\_total}}$=0$ at onset. '
    r'$\text{{HighEF}}=1$ if \texttt{{fe\_etfra}}$>0.5$. '
    r'SEs of the log-HR clustered at the conflict level in parentheses. '
    r'$^{{*}}p<0.10$, $^{{**}}p<0.05$, $^{{***}}p<0.01$.'
)


# ── Core functions ────────────────────────────────────────────────────────────

def fmt_cell(tbl, var):
    """
    Format a single (HR, SE) pair for one variable in one spec.

    Returns (hr_latex, se_latex) strings, or ('', '') if var is absent.
    HR is wrapped in $...$ so ^{***} superscripts compile without errors.
    """
    if var not in tbl.index:
        return '', ''
    r   = tbl.loc[var]
    sig = r['sig'].strip()
    hr_str = f"${r['HR']:.3f}^{{{sig}}}$" if sig else f"${r['HR']:.3f}$"
    se_str = f"({r['se']:.3f})"
    return hr_str, se_str


def build_latex_table(results_dict, specs_list, var_latex, caption, label,
                      col_headers, note_text, env='table'):
    """
    Build a LaTeX table of ClogLog hazard ratios.

    Parameters
    ----------
    results_dict : dict
        {spec_name: (summary_df, result)} as returned by fit_cloglog.
    specs_list : list of str
        Ordered list of spec names to include as columns.
    var_latex : dict
        {variable_name: latex_label_string}. Variables not in this dict
        fall back to \\texttt{variable_name}.
    caption : str
        LaTeX caption (not escaped — caller supplies valid LaTeX).
    label : str
        LaTeX label for \\ref{}.
    col_headers : dict
        {spec_name: (header_row1, header_row2)} for the two-row column header.
    note_text : str
        Text for the \\begin{tablenotes} block.
    env : str
        'table' or 'sidewaystable' (requires rotating package).

    Returns
    -------
    str
        Complete LaTeX table source.
    """
    n_cols  = len(specs_list)
    col_fmt = 'l' + (' c' * n_cols)

    # Collect all variables across specs in first-appearance order
    all_vars = []
    for s in specs_list:
        tbl, _ = results_dict[s]
        for v in tbl.index:
            if v not in all_vars:
                all_vars.append(v)

    L = [
        r'\begin{' + env + '}[H]',
        r'  \centering',
        r'  \footnotesize',
        r'  \caption{' + caption + '}',
        r'  \label{' + label + '}',
        r'  \begin{adjustbox}{max width=\textwidth}',
        r'  \begin{threeparttable}',
        r'  \begin{tabular}{' + col_fmt + '}',
        r'    \toprule',
    ]

    # Two-row column header
    h1 = '    & ' + ' & '.join(
        r'\multicolumn{1}{c}{' + col_headers[s][0] + '}' for s in specs_list
    ) + r' \\'
    h2 = '    & ' + ' & '.join(
        r'\multicolumn{1}{c}{\textit{' + col_headers[s][1] + '}}' for s in specs_list
    ) + r' \\'
    L += [h1, h2, r'    \midrule']

    # Variable rows: label & HRs on one line; blank & SEs on the next
    for var in all_vars:
        label_tex = var_latex.get(
            var, r'\texttt{' + var.replace('_', r'\_') + '}'
        )
        hr_cells, se_cells = [], []
        for s in specs_list:
            tbl, _ = results_dict[s]
            hr, se = fmt_cell(tbl, var)
            hr_cells.append(hr)
            se_cells.append(se)
        L.append(f'    {label_tex} & ' + ' & '.join(hr_cells) + r' \\')
        L.append(r'      & ' + ' & '.join(se_cells) + r' \\[4pt]')

    L.append(r'    \midrule')

    # Footer rows
    def _fmt_nobs(s):
        return f"{int(results_dict[s][0]['n_obs'].iloc[0]):,}".replace(',', '{,}')

    n_obs_row = ' & '.join(_fmt_nobs(s) for s in specs_list)
    n_evt_row = ' & '.join(
        str(int(results_dict[s][0]['n_events'].iloc[0])) for s in specs_list
    )
    aic_row   = ' & '.join(
        f"{results_dict[s][0]['aic'].iloc[0]:.1f}" for s in specs_list
    )

    L += [
        f'    Observations & {n_obs_row} \\\\',
        f'    Events       & {n_evt_row} \\\\',
        f'    AIC          & {aic_row} \\\\',
        r'    \bottomrule',
        r'  \end{tabular}',
        r'  \begin{tablenotes}[flushleft]\footnotesize',
        r'    \item ' + note_text,
        r'  \end{tablenotes}',
        r'  \end{threeparttable}',
        r'  \end{adjustbox}',
        r'\end{' + env + '}',
    ]
    return '\n'.join(L)
