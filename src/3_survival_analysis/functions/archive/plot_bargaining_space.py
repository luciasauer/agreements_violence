import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D


# ============================================================
# AUXILIARY FUNCTION
# ============================================================

def size_from_deaths(
    deaths,
    size_min=25,
    size_step=55,
    death_min=1_000,
    death_max=1_000_000
):

    deaths = np.clip(
        deaths,
        death_min,
        death_max
    )

    return (
        size_min
        +
        size_step
        *
        (
            np.log10(deaths)
            -
            np.log10(death_min)
        )
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def plot_bargaining_space(
    df,
    x,
    y,
    agreement_col="ever_agreement",
    time_col="months_to_agreement",
    deaths_col="total_deaths",
    label_col="country",
    title=""
):

    plot_df = df.copy()

    # --------------------------------------------------------
    # Bubble size
    # --------------------------------------------------------

    plot_df["point_size"] = size_from_deaths(
        plot_df[deaths_col]
    )

    # --------------------------------------------------------
    # Split groups
    # --------------------------------------------------------

    signed = plot_df[
        plot_df[agreement_col] == 1
    ]

    never = plot_df[
        plot_df[agreement_col] == 0
    ]

    # --------------------------------------------------------
    # Medians
    # --------------------------------------------------------

    x_med = plot_df[x].median()
    y_med = plot_df[y].median()

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(9,7)
    )

    # --------------------------------------------------------
    # No agreement
    # --------------------------------------------------------

    ax.scatter(
        never[x],
        never[y],
        s=never["point_size"],
        facecolors='none',
        edgecolors='#9e9e9e',
        linewidth=1.0,
        alpha=0.65,
        label='No agreement'
    )

    # --------------------------------------------------------
    # Agreement
    # --------------------------------------------------------

    sc = ax.scatter(
        signed[x],
        signed[y],
        c=np.log1p(
            signed[time_col]
        ),
        s=signed["point_size"],
        cmap='RdBu_r',
        edgecolor='white',
        linewidth=0.7,
        alpha=0.85,
        label='Agreement'
    )

    # --------------------------------------------------------
    # Median lines
    # --------------------------------------------------------

    ax.axhline(
        y_med,
        color='black',
        linestyle='--',
        lw=0.9
    )

    ax.axvline(
        x_med,
        color='black',
        linestyle='--',
        lw=0.9
    )

    # --------------------------------------------------------
    # Quadrant labels
    # --------------------------------------------------------

    quad_style = dict(
        ha='center',
        va='center',
        fontsize=8,
        color='#333333',
        bbox=dict(
            boxstyle='round,pad=0.25',
            fc='white',
            ec='#cccccc',
            alpha=0.8
        )
    )

    ax.text(
        plot_df[x].quantile(0.75),
        plot_df[y].quantile(0.75),
        'High info\nHigh commitment',
        **quad_style
    )

    ax.text(
        plot_df[x].quantile(0.25),
        plot_df[y].quantile(0.75),
        'Low info\nHigh commitment',
        **quad_style
    )

    ax.text(
        plot_df[x].quantile(0.75),
        plot_df[y].quantile(0.25),
        'High info\nLow commitment',
        **quad_style
    )

    ax.text(
        plot_df[x].quantile(0.25),
        plot_df[y].quantile(0.25),
        'Low info\nLow commitment',
        **quad_style
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    label_df = pd.concat([
        plot_df.nlargest(6, deaths_col),
        signed.nlargest(6, time_col)
    ]).drop_duplicates('conflict_id')

    for _, row in label_df.iterrows():

        ax.annotate(
            str(row[label_col]),
            xy=(row[x], row[y]),
            xytext=(4,4),
            textcoords='offset points',
            fontsize=7,
            color='#333333'
        )

    # --------------------------------------------------------
    # Colorbar
    # --------------------------------------------------------

    cbar = plt.colorbar(
        sc,
        ax=ax,
        shrink=0.78
    )

    cbar.set_label(
        'Months to first agreement (log scale)'
    )

    # --------------------------------------------------------
    # Legends
    # --------------------------------------------------------

    legend_outcome = ax.legend(
        handles=[
            Line2D(
                [0], [0],
                marker='o',
                color='w',
                markerfacecolor='#4c72b0',
                markeredgecolor='white',
                markersize=8,
                label='Agreement'
            ),
            Line2D(
                [0], [0],
                marker='o',
                color='w',
                markerfacecolor='none',
                markeredgecolor='#9e9e9e',
                markersize=8,
                label='No agreement'
            )
        ],
        loc='upper left',
        frameon=False
    )

    ax.add_artist(
        legend_outcome
    )

    # --------------------------------------------------------
    # Fatalities legend
    # --------------------------------------------------------

    size_vals = [
        1_000,
        10_000,
        100_000,
        1_000_000
    ]

    size_handles = []

    for val in size_vals:

        size_handles.append(
            plt.scatter(
                [],
                [],
                s=size_from_deaths(val),
                facecolors='none',
                edgecolors='black',
                linewidth=0.8,
                label=f'{val:,} fatalities'
            )
        )

    legend_size = ax.legend(
        handles=size_handles,
        loc='lower left',
        frameon=False,
        title='Total fatalities'
    )

    ax.add_artist(
        legend_size
    )

    # --------------------------------------------------------
    # Final aesthetics
    # --------------------------------------------------------

    ax.set_xlabel(x)
    ax.set_ylabel(y)

    ax.set_title(title)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.grid(alpha=0.25)

    plt.tight_layout()

    return fig, ax