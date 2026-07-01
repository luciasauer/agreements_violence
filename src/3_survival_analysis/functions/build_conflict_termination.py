import pandas as pd


# ============================================================
# OUTCOME LABELS
# ============================================================

OUTCOME_LABELS = {
    1: 'Peace agreement',
    2: 'Ceasefire',
    3: 'Victory (govt)',
    4: 'Victory (rebels)',
    5: 'Low activity',
    6: 'Actor ceases to exist'
}

# ============================================================
# GROUPED OUTCOMES
# ============================================================

OUTCOME_GROUPS = {
    1: 'Agreement',
    2: 'Ceasefire',
    3: 'Military victory',
    4: 'Military victory',
    5: 'Low activity',
    6: 'Actor ceases'
}


# ============================================================
# MAIN FUNCTION
# ============================================================

def build_conflict_termination(
    df_panel,
    termination_path
):

    # --------------------------------------------------------
    # Load termination dataset
    # --------------------------------------------------------

    df_termination = pd.read_csv(
        termination_path
    )

    # --------------------------------------------------------
    # Keep only ended episodes
    # --------------------------------------------------------

    df_episodes = df_termination[
        df_termination['c_epterm'] == 1
    ].copy()

    # --------------------------------------------------------
    # Extract LAST episode per conflict
    # --------------------------------------------------------
    # Highest c_epno = most recent episode
    # --------------------------------------------------------

    last_episode = (
        df_episodes
        .sort_values(
            ['conflict_id', 'c_epno']
        )
        .groupby('conflict_id')
        .last()
        .reset_index()
        [
            [
                'conflict_id',
                'c_epno',
                'c_outcome',
                'c_ep_endyear',
                'c_ep_durcount'
            ]
        ]
    )

    # --------------------------------------------------------
    # Create readable labels
    # --------------------------------------------------------

    last_episode['termination_outcome_label'] = (
        last_episode['c_outcome']
        .map(OUTCOME_LABELS)
    )

    last_episode['termination_outcome_group'] = (
        last_episode['c_outcome']
        .map(OUTCOME_GROUPS)
    )

    # --------------------------------------------------------
    # Fill ongoing conflicts
    # --------------------------------------------------------

    last_episode['termination_outcome_label'] = (
        last_episode['termination_outcome_label']
        .fillna('Ongoing / censored')
    )

    last_episode['termination_outcome_group'] = (
        last_episode['termination_outcome_group']
        .fillna('Ongoing / censored')
    )

    # --------------------------------------------------------
    # Merge into panel
    # --------------------------------------------------------

    df_panel = df_panel.merge(
        last_episode[
            [
                'conflict_id',
                'c_outcome',
                'termination_outcome_label',
                'termination_outcome_group',
                'c_ep_endyear',
                'c_epno',
                'c_ep_durcount'
            ]
        ],
        on='conflict_id',
        how='left'
    )

    # --------------------------------------------------------
    # Conflicts with no termination record
    # --------------------------------------------------------

    df_panel['termination_outcome_label'] = (
        df_panel['termination_outcome_label']
        .fillna('Ongoing / censored')
    )

    df_panel['termination_outcome_group'] = (
        df_panel['termination_outcome_group']
        .fillna('Ongoing / censored')
    )

    return df_panel