From the V-Dem Core dataset we download the following indicators:

## V-Dem variables: definitions and theoretical classification

The table below describes each variable extracted from the V-Dem dataset (v16),
its direction of coding, and its role as a proxy for commitment problems or
informational asymmetries in the bargaining-failure framework.

**Direction convention:** "Higher = more commitment problem" means the variable
enters the commitment index directly. "Higher = less commitment problem" means
the variable must be inverted (multiplied by −1) before entering the index.

| Variable name | V-Dem code | Barrier type | Definition | Direction |
|---|---|---|---|---|
| `state_territorial_control` | `v2svstterr` | Commitment | Extent to which the government exercises de facto control over its territory. Low values indicate that armed non-state actors contest sovereignty over parts of the country — the government cannot credibly commit to protect rebel groups that disarm if it does not even control the territory. | Higher = less commitment problem → **invert** |
| `domestic_autonomy` | `v2svdomaut` | Commitment | Degree to which the government is free from de facto interference by domestic actors (warlords, militias, economic elites) in its sovereign decisions. Low autonomy means the government cannot bind the state to future behaviour independently of those actors. | Higher = less commitment problem → **invert** |
| `fiscal_capacity` | `v2stfisccap` | Commitment | Extent to which the state derives revenue from broad-based taxation rather than from a narrow resource base or external transfers. States with low fiscal capacity are more dependent on controlling rents (oil, minerals, aid), making post-settlement commitment to share power less credible. | Higher = less commitment problem → **invert** |
| `meritocracy_state` | `v2stcritrecadm` | Commitment | Degree to which appointments in the state administration are based on merit rather than personal loyalty or ethnic/political affiliation. Low meritocracy signals a patronage state where the incumbent's hold on power depends on controlling appointments — a structural incentive to avoid power-sharing agreements. | Higher = less commitment problem → **invert** |
| `meritocracy_army` | `v2stcritapparm` | Commitment | Same as above but for the armed forces. An army appointed on the basis of loyalty rather than merit is an instrument of the ruler, not of the state — making credible demobilisation and DDR commitments harder. | Higher = less commitment problem → **invert** |
| `neopatrimonial` | `v2x_neopat` | Commitment + Political bias | Composite index of neopatrimonial rule, combining clientelism, presidentialism, and regime corruption. High values indicate that the leader governs through personal networks rather than institutions — the leader cannot credibly commit the state to post-settlement behaviour because the state *is* the leader. This is the primary proxy for personalised rule, replacing the GWF dataset. | Higher = more commitment problem → **use directly** |
| `clientelism` | `v2xnp_client` | Political bias | Sub-component of `v2x_neopat`. Measures the degree to which political support is mobilised through the distribution of private goods (jobs, contracts, favours) rather than programmatic policies. A clientelist leader needs to control state resources to maintain loyalty — creating a private benefit from continued conflict. | Higher = more political bias → **use directly** |
| `presidentialism` | `v2xnp_pres` | Political bias | Sub-component of `v2x_neopat`. Measures the concentration of executive power in the president relative to other state institutions. High presidentialism means fewer institutional constraints on the executive's decision to continue or end conflict. | Higher = more political bias → **use directly** |
| `regime_corruption` | `v2xnp_regcorr` | Political bias | Sub-component of `v2x_neopat`. Measures the extent to which the political regime is based on corrupt exchanges — bribes, kickbacks, misappropriation of public funds. High regime corruption implies the leader derives private rents from controlling state power, increasing the opportunity cost of peace. | Higher = more political bias → **use directly** |
| `horiz_accountability` | `v2x_horacc` | Informational asymmetry | Composite index of horizontal accountability: the extent to which state institutions (courts, legislature, audit agencies) can hold the executive accountable. High accountability implies more transparent governance and more credible information flows between the state and non-state actors — reducing informational barriers. | Higher = less informational asymmetry → **invert** |
| `judicial_constraints` | `v2x_jucon` | Informational asymmetry | Extent to which the judiciary can constrain executive action in practice. An independent judiciary signals that the government is bound by rules it cannot unilaterally change — making its stated positions more credible and reducing uncertainty about its type and resolve. | Higher = less informational asymmetry → **invert** |
| `legislative_constraints` | `v2xlg_legcon` | Informational asymmetry | Extent to which the legislature can constrain the executive in practice. Legislative oversight creates public information about government decisions and limits the government's ability to misrepresent its capabilities or intentions. | Higher = less informational asymmetry → **invert** |
| `regime_type` | `v2x_regime` | Informational asymmetry | Ordinal classification of regime type from the Regimes of the World (RoW) index: 0 = closed autocracy, 1 = electoral autocracy, 2 = electoral democracy, 3 = liberal democracy. More democratic regimes have greater press freedom, legislative oversight, and institutional transparency — all of which reduce the government's capacity to maintain private information about its capabilities and resolve. | Higher = less informational asymmetry → **invert** |

## Notes on index construction

**Commitment index (PCA):** The four components proposed by Laura map to the
following variables. All are inverted before entering the PCA so that high
scores on the index consistently indicate more severe commitment problems.

| Laura's component | Variable used | Transformation |
|---|---|---|
| Number of active armed factions | `mean_factions` (from UCDP GED) | None — higher = more fragmentation |
| Inverse of V-Dem state capacity | `state_territorial_control` | Multiply by −1 |
| Personalistic regime indicator | `neopatrimonial` (`v2x_neopat`) | None — higher = more personalist |
| Gov. incompatibility | `governmental` (from UCDP ACD) | None — 1 = governmental conflict |

**Informational asymmetry index:** The V-Dem variables (`horiz_accountability`,
`judicial_constraints`, `legislative_constraints`, `regime_type`) are all
inverted before entering a parallel PCA, so that high scores indicate higher
informational barriers to settlement.

**Note on collinearity:** `neopatrimonial`, `clientelism`, `presidentialism`,
and `regime_corruption` are sub-components of the same composite index and will
be highly correlated. For the PCA, use only `neopatrimonial` (`v2x_neopat`) as
the single representative of this dimension to avoid multicollinearity inflating
one component of the index.