# Bargaining Model: Why Do So Few Conflicts Reach Agreements?

## Motivation

We have established that entering a peace process — defined in our analysis as the signature of the first agreement — reduces violence. This is an important finding, but it raises a deeper and arguably more puzzling question:

> If agreements work, why do so few conflicts actually reach one?

In our sample of 201 conflicts, only 71 ever sign an agreement. Understanding why the remaining 130 never do is the central question of this section. We also ask how those 130 conflicts end: do they terminate through military victory, low activity, or do they remain ongoing?

---

## Theoretical Framework

The bargaining theory of war provides the organizing framework. War persists because of barriers to bargaining. Fearon (1995) identifies two canonical barriers:

**Information asymmetries.** The parties do not know enough about each other's strength, resolve, or probability of victory to identify mutually acceptable terms. Fighting resolves this barrier: each engagement reveals private information. From this perspective, information-barrier conflicts carry the seeds of their own resolution — once the information gap closes, the conditions for a deal emerge naturally.

**Commitment problems.** The parties can identify acceptable terms but cannot credibly commit to honoring them. Fighting does not resolve this barrier — it exacerbates it. Combat destroys the institutions that could enforce agreements, deepens distrust, and entrenches the conditions that made commitment incredible in the first place.

### The Key Asymmetry

The crucial difference between these two barriers is what fighting does to each of them:

- In **information-barrier conflicts**, fighting is productive. It reveals private information and progressively closes the gap between what each side knows and what would be needed to agree.
- In **commitment-barrier conflicts**, fighting is destructive in a deeper sense. It does not generate the conditions for agreement — only accumulated catastrophe can push these conflicts toward a deal, and even then the agreement remains fragile.

This asymmetry implies two qualitatively different paths to agreement, rather than a single story about how conflicts resolve.

---

## Hypotheses

### H1 — Selection into treatment

Commitment-dominant conflicts are less likely to reach peace agreements. Among the 201 conflicts in our sample, the 130 that never sign should disproportionately exhibit commitment-barrier characteristics: multiple armed factions, personalist regimes, and weak state capacity.

**Test:** In a logit model for the probability of ever signing an agreement, commitment-problem proxies should have negative coefficients. This is consistent with the preliminary finding that the presence of multiple simultaneous conflicts reduces agreement probability by approximately 67%.

### H2 — Timing of agreement

Among conflicts that do reach agreements, information-dominant conflicts should sign earlier. If the information gap closes with fighting, these conflicts should reach the conditions for a deal relatively fast. Commitment-dominant conflicts should sign later, and only after extreme accumulated violence — the *destruction channel*.

**Test:** In a discrete-time hazard model for time to first agreement, information-asymmetry proxies should predict earlier signing (higher hazard), while commitment-problem proxies should predict later signing (lower hazard). The finding that every high-intensity conflict eventually signs is consistent with the destruction channel operating for commitment-dominant conflicts.

### H3 — Heterogeneous treatment effects

The violence-reducing effect of agreements should be larger and more persistent for information-dominant conflicts, and smaller or fading for commitment-dominant conflicts.

**Test:** Split the Callaway and Sant'Anna event study by conflict type using the information-asymmetry vs. commitment classification. The predicted pattern is that post-agreement violence reductions are steeper and longer-lasting for information-dominant conflicts.

### H4 — Agreement design on the commitment path

Among commitment-dominant conflicts, agreements with stronger provisions — power-sharing, DDR, third-party monitoring, security sector reform — should have larger treatment effects. Among information-dominant conflicts, provision quality should matter less, because the agreement mainly serves as a coordination device once the information gap has closed.

**Test:** Interact the treatment effect with a provisions-quality index constructed from PA-X agreement content tags. The interaction should be significant for commitment-dominant conflicts but not for information-dominant ones.

---

## Proxy Construction

To test these hypotheses, we need to classify conflicts along the information-asymmetry and commitment-problem dimensions. We construct proxies for each friction family, then use them to build indices that allow conflict-level classification.

### Information asymmetry proxies

These variables capture how much uncertainty remains between the parties about each other's capabilities and resolve.

| Proxy | Rationale |
|---|---|
| Past conflict experience | Prior fighting between the same parties reveals capabilities and reduces uncertainty at the start of a new episode |



### Commitment problem proxies

These variables capture how difficult it is for the parties to make credible commitments — whether institutions exist to enforce agreements.

| Proxy | Rationale |
|---|---|
| Checks and balances (judicial, legislative, horizontal accountability) | Stronger institutional constraints make it harder for a government to unilaterally defect after signing |
| Regime stability | Frequently changing regimes cannot credibly commit to long-term agreements |


### Political bias proxies

These variables capture whether leaders have personal incentives that diverge from a negotiated settlement.

| Proxy | Rationale |
|---|---|
| Regime type | Personalist leaders face less accountability and can pursue war for personal benefit at lower political cost |
| Leader characteristics (wealth, industry links) | Leaders with economic stakes in conflict industries have material incentives to prolong fighting |

---

## Data Sources

| Proxy family | Variable | Dataset | Key field |
|---|---|---|---|
| Information asymmetry | Past conflict experience | UCDP Dyadic v25.1 (already built) | Constructed variable |
| Information asymmetry | Number of groups | UCDP Dyadic v25.1 | Count `dyad_id` per `conflict_id × year` |
| Information asymmetry | Terrain | PRIO-GRID v3 | `mountains_mean` aggregated to country |
| Commitment problems | Checks and balances | V-Dem v14 | `v2x_jucon`, `v2xlg_legcon` |
| Commitment problems | Regime stability | Polity 5 | `durable` |
| Commitment problems | State capacity | World Bank WGI | `GE.EST` (Government Effectiveness) |
| Political bias | Regime type | GWF (Geddes Wright Frantz) | `gwf_regimetype` |
| Political bias | Leader characteristics | REIGN | `personal_loyalty`, `military_support` |

---

## Empirical Strategy

1. **Merge** external datasets (V-Dem, Polity 5, WGI, GWF, UCDP Dyadic) into the conflict panel using `isocode × year`, with a one-year lag for time-varying institutional variables to avoid contemporaneous endogeneity.
2. **Construct indices** for each friction family using standardized additive indices and PCA as a robustness check.
3. **Classify conflicts** as information-dominant or commitment-dominant based on their index profiles at conflict onset (using pre-conflict period values).
4. **Test H1** with a cross-sectional logit (N = 201 conflicts).
5. **Test H2** with a discrete-time complementary log-log hazard model on the conflict-month panel.
6. **Test H3** by running separate Callaway–Sant'Anna event studies for each conflict type.
7. **Test H4** by interacting the treatment effect with a PA-X provisions-quality index, estimated within the commitment-dominant subsample.