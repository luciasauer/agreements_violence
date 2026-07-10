# ClogLog Results — Interpretation Notes

**Model:** Discrete-time cause-specific ClogLog hazard (competing risks).  
**Outcomes:** Signing (S), Victory (V), Fade (F).  
**Baseline specs:** M1–M6 (log-age), M1b–M6b (age-bins), M1c–M6c (age-bins + decade controls).  
**Coefficients reported as hazard ratios (HR = exp(β)). HR > 1 accelerates the event; HR < 1 delays it.**

Results discussed below correspond to the **log-age baseline (M4/M5)** unless otherwise noted.

---

## General Framework

The CP proxy variables are designed to capture situations where parties cannot credibly commit to honoring a peace agreement (Fearon 1995). Higher CP → harder to reach agreements → **expected HR < 1 for signing**.

For victory and fade the theoretical direction is less direct and must be derived case by case.

---

## 1. `defpact_majpow_onset` — Third-party security guarantees

**Theoretical logic.** A defense pact with a major power at conflict onset can be read in two opposite ways:
- As an *external enforcement device*: reduces the commitment problem → expected HR > 1 for signing.
- As *external military backing for one party*: gives them incentives to fight to victory rather than negotiate → expected HR > 1 for victory, HR for signing ambiguous.

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | Ambiguous (±) |
| Victory | HR > 1 (backed party can achieve military win) |
| Fade | HR < 1 (externally-backed conflicts do not quietly expire) |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | 1.374 | 1.863 | No | Inconclusive |
| Victory | 1.491 | **6.989** | Yes (M5, p<0.05) | ✓ Strong |
| Fade | 0.909 | 0.628 | No | Direction correct |

**Key finding.** The most striking result is that a defense pact multiplies the victory hazard by ~7 in M5. This suggests that when a major power backs one side, conflicts tend to be resolved militarily rather than diplomatically. The signing hazard goes in the positive direction but is not significant.

---

## 2. `loot_onset` — Lootable resources

**Theoretical logic.** Lootable natural resources (diamonds, drugs) create commitment problems because the party controlling resources after an agreement has incentives to renege — resource rents make continued fighting financially attractive (Collier & Hoeffler; Ross). Expected HR < 1 for signing.

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | HR < 1 (resources make defection from peace attractive) |
| Victory | Ambiguous |
| Fade | HR < 1 (resources sustain fighting incentives, conflicts persist) |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | 1.196 | 0.958 | No | No — unexpected direction in M4, near zero in M5 |
| Victory | 1.818 | 0.585 | No | Inconclusive |
| Fade | 0.739 | 0.824 | No | Direction correct, not significant |

**Key finding.** No statistically significant effect on any outcome. The null result on signing is notable — one possible explanation is that lootable resources are endogenous to conflict intensity, and their variation is already absorbed by the conflict-age controls.

---

## 3. `mountains_onset` — Mountainous terrain (fraction)

**Theoretical logic.** Rugged terrain favors rebel groups, who can hold mountain territory and retreat into it. This creates commitment problems: the government cannot verify disarmament of groups that retain mountain strongholds. Expected HR < 1 for signing. For fade: mountain conflicts are expected to persist (HR < 1).

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | HR < 1 (terrain makes commitment harder) |
| Victory | HR < 1 (hard for either side to achieve decisive victory) |
| Fade | HR < 1 (conflicts in mountains do not quietly expire) |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | 1.324 | 0.848 | No | Sign flips across specs; inconclusive |
| Victory | 0.956 | 0.506 | No | Direction correct in M5, not significant |
| Fade | **0.390** | 1.391 | Yes (M4, p<0.10) | ✓ In M4 |

**Key finding.** The clearest result is the significant negative effect on fade in M4: mountainous conflicts do not quietly expire — they persist. The signing coefficient is unstable (changes sign with the interaction) and never reaches significance. Overall, the terrain variable is most informative about conflict persistence rather than the signing channel.

---

## 4. `bdist_onset` — Distance to nearest border (km)

**Theoretical logic.** Conflicts near a border give rebels access to cross-border sanctuaries — they can retreat, regroup, and return. This creates commitment problems because the government cannot verify rebel disarmament when rebel forces can cross borders freely. Expected: smaller `bdist` (closer to border) → more CP → lower signing hazard, so **HR > 1** (more distance = less CP = more likely to sign).

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | HR > 1 (further from border = fewer cross-border options = easier to commit) |
| Victory | Ambiguous |
| Fade | Ambiguous |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | **0.996** | 0.994 | Yes (M4, p<0.01) | ✗ Direction opposite to expectation |
| Victory | 0.996 | 0.999 | No | Inconclusive |
| Fade | 0.999 | 1.004 | No | Null |

**Key finding.** The effect on signing is statistically significant and improves AIC by ~6 points, but the direction is the *opposite* of the theoretical prediction: conflicts further from the border are *less* likely to sign. A possible alternative interpretation: conflicts far from borders tend to be government-type conflicts (about power in the capital, not territory) which are inherently harder to resolve. The per-km effect is small (HR = 0.996) but at scale meaningful: 100 additional km from border ≈ 33% lower signing hazard.

---

## 5. `capdist_onset` — Distance to capital (km)

**Theoretical logic.** Conflicts further from the capital occur where the government has weaker power projection capacity, creating power-shift risk: rebels in remote areas can consolidate territory that the government cannot retake, making any agreement less credible. Expected HR < 1 for signing.

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | HR < 1 (remote conflicts → power shift risk → harder to commit) |
| Victory | HR < 1 (government finds it harder to achieve decisive victory remotely) |
| Fade | Ambiguous |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | 1.000 | 1.000 | No | Null — no effect |
| Victory | 1.000 | 1.000 | No | Null |
| Fade | 1.000 | 0.999 | No | Null |

**Key finding.** This variable has essentially no predictive power in any specification. Likely reasons: (1) `capdist` is highly correlated with country size and with `bdist`, providing no marginal information once other controls are included; (2) the per-km effect is too small to be detected with this sample size (98 signing events, 33 victory events, 31 fade events).

---

## 6. `territorial_incompatibility` — Issue indivisibility

**Theoretical logic.** Territorial conflicts are argued to be harder to resolve (Fearon 1995: the "issue indivisibility" problem). While territory is physically divisible, strategic territories (ethnic homelands, resource-rich areas, borders) can be effectively indivisible, creating commitment problems about post-agreement territorial control. Expected HR < 1 for signing. For fade: territorial conflicts are expected to persist (HR < 1), not fade quietly.

**Expected signs:**

| Outcome | Theoretical expectation |
|---|---|
| Signing | HR < 1 (indivisibility makes agreement harder) |
| Victory | Ambiguous (territory may have clearer military resolution) |
| Fade | HR < 1 (territorial conflicts persist) |

**Results (M4 / M5):**

| Outcome | HR M4 | HR M5 | Significant? | Consistent with theory? |
|---|---|---|---|---|
| Signing | 0.885 | 0.621 | No | ✓ Direction correct, not significant |
| Victory | 0.960 | **0.142** | Yes (M5, p<0.05) | Complex — see below |
| Fade | **3.337** | 11.347 | Yes (M4, p<0.05) | ✗ Opposite direction |

**Key findings:**

- **Victory with interaction (M5):** The main effect HR = 0.142** means that territorial conflicts at early ages have a much *lower* hazard of military victory. However, the interaction coefficient HR = 2.899** means this effect reverses with conflict age — in long-running territorial conflicts, the hazard of victory eventually increases. Interpretation: achieving military victory over territorial disputes is very difficult initially, but when it happens it tends to be in protracted conflicts.

- **Fade:** The result HR = 3.337** is the most counterintuitive finding across all CP variables — territorial conflicts have a *much higher* fade rate. This contradicts the prior that territorial conflicts are persistent. One possible interpretation: when territorial incompatibility cannot be resolved militarily or diplomatically, the conflict simply loses intensity and drifts to low-activity status. Government-type conflicts, by contrast, involve control of the state itself and maintain intensity longer.

---

## Summary Table

| Variable | Signing expected | Signing found | Victory found | Fade found | Overall |
|---|---|---|---|---|---|
| `defpact_majpow_onset` | Ambiguous | Null | **↑↑ strong** | Null | Dominant in victory channel |
| `loot_onset` | HR < 1 | Null | Null | Null | No effect |
| `mountains_onset` | HR < 1 | Null/unstable | Null | **↓ significant** | Persistence channel only |
| `bdist_onset` | HR > 1 | **0.996*** (opposite)** | Null | Null | Significant but unexpected sign |
| `capdist_onset` | HR < 1 | Null | Null | Null | No effect |
| `territorial_incompatibility` | HR < 1 | Correct direction (ns) | **Complex** | **↑ counterintuitive** | Strongest effects in V and F |
