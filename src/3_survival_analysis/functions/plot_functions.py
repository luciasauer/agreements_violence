# This file will contain several functions to plot different figures
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

# Plot conflict termination distribution
outcome_order = [
    "Military victory",
    "Low activity",
    "Ceasefire",
    "Actor ceases",
    "Ongoing / censored",
    "Agreement"
]

colors_map = {
    "Military victory":   "#2E327D",
    "Low activity":       "#F3B87D",
    "Ceasefire":          "#C94141",
    "Actor ceases":       "#546E7A",
    "Ongoing / censored": "#B0BEC5",
    "Agreement":          "#1565C0",
}

# ============================================================
# 4. GENERIC PLOTTING FUNCTION
# ============================================================

def plot_termination_distribution(
    df,
    split_var,
    title,
    split_labels=None
):

    # --------------------------------------------------------
    # Aggregate outcomes
    # --------------------------------------------------------

    grouped = (
        df
        .groupby(
            [
                split_var,
                "termination_outcome_group"
            ]
        )
        .size()
        .reset_index(name="n")
    )

    # --------------------------------------------------------
    # Percentages within group
    # --------------------------------------------------------

    totals = grouped.groupby(
        split_var
    )["n"].transform("sum")

    grouped["pct"] = (
        grouped["n"]
        /
        totals
        * 100
    )

    # --------------------------------------------------------
    # Pivot table
    # --------------------------------------------------------

    pivot = (
        grouped
        .pivot(
            index=split_var,
            columns="termination_outcome_group",
            values="pct"
        )
        .fillna(0)
    )

    # --------------------------------------------------------
    # Reorder columns
    # --------------------------------------------------------

    pivot = pivot.reindex(
        columns=[
            c for c in outcome_order
            if c in pivot.columns
        ]
    )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(7,5)
    )

    bottom = np.zeros(len(pivot))

    # --------------------------------------------------------
    # X labels
    # --------------------------------------------------------

    if split_labels is not None:

        x_labels = [
            split_labels[k]
            for k in pivot.index
        ]

    else:

        x_labels = pivot.index.astype(str)

    # --------------------------------------------------------
    # Plot stacked bars
    # --------------------------------------------------------

    for col in pivot.columns:

        bars = ax.bar(
            x_labels,

            pivot[col],

            bottom=bottom,

            color=colors_map[col],

            edgecolor="white",
            linewidth=0.7,

            width=0.6,

            label=col
        )

        # ----------------------------------------------------
        # Labels inside bars
        # ----------------------------------------------------

        for j, (
            bar,
            val
        ) in enumerate(zip(bars, pivot[col])):

            if val > 7:

                ax.text(
                    bar.get_x()
                    +
                    bar.get_width()/2,

                    bottom[j]
                    +
                    val/2,

                    f"{val:.0f}%",

                    ha="center",
                    va="center",

                    fontsize=8,
                    color="white",
                    fontweight="bold"
                )

        bottom += pivot[col].values

    # --------------------------------------------------------
    # Aesthetics
    # --------------------------------------------------------

    ax.set_ylim(0,105)

    ax.set_ylabel(
        "Share of conflicts (%)",
        fontsize=10
    )

    ax.set_title(
        title,
        fontsize=11
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda x, _: f"{x:.0f}%"
        )
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    handles = [

        mpatches.Patch(
            color=colors_map[c],
            label=c
        )

        for c in outcome_order
        if c in pivot.columns
    ]

    ax.legend(
        handles=handles,

        frameon=False,

        fontsize=8,

        loc="upper center",

        bbox_to_anchor=(0.5, 1.02),

        ncol=1
    )

    plt.tight_layout()

    return fig, ax



# ============================================================
# KDE PLOT FUNCTION by agreement status
# ============================================================

def plot_kde_by_agreement(
    df,
    variable,
    label,
    ax,
    color_noagr,
    color_agr
):

    # Split groups
    g0 = df.loc[
        df['ever_agreement'] == 0,
        variable
    ].dropna()

    g1 = df.loc[
        df['ever_agreement'] == 1,
        variable
    ].dropna()

    # KDE plots
    sns.kdeplot(
        g0,
        ax=ax,
        color=color_noagr,
        lw=1.8,
        label=f'No agreement (n={len(g0)})'
    )

    sns.kdeplot(
        g1,
        ax=ax,
        color=color_agr,
        lw=1.8,
        linestyle='--',
        label=f'Agreement (n={len(g1)})'
    )

    # Mean lines
    ax.axvline(
        g0.mean(),
        color=color_noagr,
        lw=0.8,
        ls=':',
        alpha=0.7
    )

    ax.axvline(
        g1.mean(),
        color=color_agr,
        lw=0.8,
        ls=':',
        alpha=0.7
    )

    # T-test
    t_stat, p_val = stats.ttest_ind(
        g0,
        g1,
        nan_policy='omit'
    )

    p_text = (
        f'p = {p_val:.3f}'
        if p_val >= 0.001
        else 'p < 0.001'
    )

    ax.text(
        0.97,
        0.93,
        p_text,
        transform=ax.transAxes,
        ha='right',
        va='top',
        fontsize=8,
        color='#555555',
        bbox=dict(
            boxstyle='round,pad=0.2',
            fc='white',
            ec='#cccccc',
            lw=0.5
        )
    )

    # Labels
    ax.set_title(label, fontsize=9)
    ax.set_ylabel('Density', fontsize=8)
    ax.set_xlabel('')

    ax.legend(fontsize=7)

    ax.yaxis.set_major_formatter(
        mticker.FormatStrFormatter('%.2f')
    )


# ============================================================
# SPELL PANEL: survival analysis risk-set visualisation
# ============================================================

# year_mo_numeric=1 corresponds to 1989-01 in the conflict panel
_BASE_PERIOD = pd.Period('1989-01', freq='M')

def _numeric_to_timestamp(n):
    return (_BASE_PERIOD + int(n) - 1).to_timestamp()


def _to_timestamp(val):
    """Convert a date value to Timestamp.

    Handles: pd.Timestamp, pd.Period, numeric month index (year_mo_numeric),
    and 'YYYY-MM' strings.
    """
    if pd.isna(val):
        return pd.NaT
    if isinstance(val, pd.Timestamp):
        return val
    if isinstance(val, pd.Period):
        return val.to_timestamp()
    if isinstance(val, int | float | np.integer | np.floating):
        return _numeric_to_timestamp(int(val))
    return pd.Timestamp(str(val)[:7] + '-01')


def plot_spell_panel(df_conflict, sort_by='start', save_path=None,
                     start_date_column='start_date',
                     end_date_column='end_date',
                     period_column='year_mo_numeric',
                     agreement_indicator_column='ever_agreement'):
    """
    Horizontal-line panel of conflict spells used in the survival analysis.

    Works with monthly and quarterly panels. For quarterly panels pass:
        start_date_column='start_date_q',
        end_date_column='end_date_q',
        period_column='yq'

    Each row is one conflict. The line runs from start to:
      - agreement date  → treated (blue, vertical-bar endpoint)
      - end_date        → right-censored (grey, arrow endpoint)

    Parameters
    ----------
    df_conflict : DataFrame
        Conflict panel (monthly or quarterly).
    sort_by : 'start' | 'end'
        Sort conflicts by start date (default) or spell-end date.
    save_path : str or None
        If provided, save the figure to this path.
    start_date_column : str
        Column with conflict start date.
    end_date_column : str
        Column with conflict end date.
    period_column : str
        Time-axis column whose max value per conflict gives the agreement date
        (spell is already trimmed at first agreement for treated conflicts).
        Monthly: 'year_mo_numeric'. Quarterly: 'yq'.
    agreement_indicator_column : str
        Binary column flagging treated conflicts.
    """

    # ----------------------------------------------------------
    # Build conflict-level summary
    # ----------------------------------------------------------
    conflicts = (
        df_conflict
        .groupby('conflict_id')
        .agg(
            _start=(start_date_column, 'first'),
            _end=(end_date_column, 'first'),
            ever_agreement=(agreement_indicator_column, 'first'),
            _period_max=(period_column, 'max'))
    ).reset_index()

    conflicts['start_dt']    = conflicts['_start'].apply(_to_timestamp)
    conflicts['end_dt']      = conflicts['_end'].apply(_to_timestamp)
    conflicts['agreement_dt'] = conflicts.apply(
        lambda r: _to_timestamp(r['_period_max']) if r['ever_agreement'] else pd.NaT,
        axis=1,
    )

    # Spell end: agreement date for treated, end_date for censored
    conflicts['spell_end_dt'] = np.where(
        conflicts['ever_agreement'] == 1,
        conflicts['agreement_dt'],
        conflicts['end_dt'],
    )
    conflicts['spell_end_dt'] = pd.to_datetime(conflicts['spell_end_dt'])

    # ----------------------------------------------------------
    # Sort
    # ----------------------------------------------------------
    if sort_by == 'end':
        conflicts = conflicts.sort_values(
            ['spell_end_dt', 'start_dt'], ascending=[False, True]
        ).reset_index(drop=True)
    else:
        conflicts = conflicts.sort_values(
            ['start_dt', 'spell_end_dt'], ascending=[True, True]
        ).reset_index(drop=True)

    # ----------------------------------------------------------
    # Figure
    # ----------------------------------------------------------
    n = len(conflicts)
    fig_height = max(8, n * 0.07)
    fig_width  = 170 / 25.4  # ~6.7 in

    fig, ax = plt.subplots(figsize=(5, 3))

    COLOR_TREATED  = '#1565C0'
    COLOR_CENSORED = '#9E9E9E'

    for i, row in conflicts.iterrows():
        color = COLOR_TREATED if row['ever_agreement'] else COLOR_CENSORED
        # Horizontal spell line
        ax.plot(
            [row['start_dt'], row['spell_end_dt']],
            [i, i],
            color=color,
            linewidth=0.7,
            alpha=0.85,
            solid_capstyle='butt',
        )
        # Endpoint marker
        if row['ever_agreement']:
            ax.plot(
                row['spell_end_dt'], i,
                '|', color=color, markersize=3.5, markeredgewidth=1.0,
            )
        else:
            ax.plot(
                row['spell_end_dt'], i,
                4,  # matplotlib marker code for right-pointing triangle
                color=color, markersize=3, markeredgewidth=0.0,
            )

    # ----------------------------------------------------------
    # Axes
    # ----------------------------------------------------------
    ax.set_xlim(
        pd.Timestamp('1989-01-01'),
        pd.Timestamp('2024-12-01'),
    )
    ax.set_ylim(-1, n)

    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')

    ax.set_yticks([])
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel(f'', fontsize=9)
    ax.set_title('Conflict spells — survival analysis risk set', fontsize=10)

    # ----------------------------------------------------------
    # Legend
    # ----------------------------------------------------------
    n_treated  = int(conflicts['ever_agreement'].sum())
    n_censored = n - n_treated

    legend_handles = [
        mlines.Line2D(
            [], [], color=COLOR_TREATED, linewidth=1.5,
            label=f'Reaches first agreement (n={n_treated})',
        ),
        mlines.Line2D(
            [], [], color=COLOR_CENSORED, linewidth=1.5,
            label=f'Right-censored (n={n_censored})',
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc='upper left',
        frameon=False,
        fontsize=8,
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')

    return fig, ax