<h1 align="center">Agreements and Violence</h1>

<p align="center">
  <b>Principal Investigators:</b> Laura Mayoral · Hannes Müller · Dominic Rohner · Christopher Rauh <br>
  <b>Research Assistant:</b> Lucia Sauer
</p>
<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python" alt="Python Badge">
  <img src="https://img.shields.io/badge/Stata-17-blue" alt="Stata Badge">
  <img src="https://img.shields.io/badge/uv-venv-orange" alt="uv Badge">
</p>

---

## Overview

Do peace agreements reduce violence — and why do so few conflicts produce them?

This project estimates the causal effect of **first peace agreements** on conflict fatalities using a staggered difference-in-differences design, and studies the determinants of agreement formation through a **Fearon (1995) bargaining framework**.

> **Data:** 201 armed conflicts · 1989–2024 · conflict × month panel  
> **Agreements:** PA-X v9 (71 conflicts ever sign; 130 never do)  
> **Fatalities:** UCDP GED v25.1

---

## Research Design

### Part I — Causal Effect of Agreements on Violence

**Treatment:** The *first* peace agreement signed in each conflict (PA-X), which marks entry into the peace process.

**Activity filter:** Conflicts must have ≥ 12 battle deaths in the quarterly window (two quarters before the agreement + the agreement quarter). This yields **66 treated conflicts** out of 71 that ever sign; 5 are reclassified as never-treated due to near-zero pre-agreement violence.

**Estimator:** Callaway and Sant'Anna (2021) doubly robust DiD (`csdid2`, `drimp`), with not-yet-treated and never-treated conflicts as the comparison group. Panel collapsed to **quarterly frequency**; event window ±8 quarters.

```math
ATT(g,t) = \mathbb{E}[Y_{it}(g) - Y_{it}(0) \mid G_i = g]
```

**Main results — quarterly CSDID (outcome: ln fatalities + 1)**

| Specification | Pre-avg ATT | Post-avg ATT | SE | p |
|:--|--:|--:|--:|:--|
| CS-1: Unconditional | −0.183 | **−1.132** | 0.395 | < 0.01 |
| CS-2: Doubly robust | −0.037 | **−0.969** | 0.466 | < 0.05 |

The estimated post-treatment average effect of **−1.0 log points** (≈ 63% reduction in fatalities) is robust across quarterly and semi-annual aggregation, and is pre-trend-free.

<div align="center" style="display: flex; justify-content: center; gap: 20px; margin: 16px 0;">
  <div style="text-align: center;">
    <img src="src/3_causal_effect_estimation/3_0_csdid/results/csdid_event_qtr_nocov.png" width="440">
    <p><em>CS-1: Unconditional</em></p>
  </div>
  <div style="text-align: center;">
    <img src="src/3_causal_effect_estimation/3_0_csdid/results/csdid_event_qtr_cov.png" width="440">
    <p><em>CS-2: Doubly robust (pre-violence + conflict age)</em></p>
  </div>
</div>

---

### Part II — Why Do So Few Conflicts Reach Agreements?

We classify conflicts along two Fearon (1995) friction dimensions and test whether these predict agreement formation and timing.

| Friction | Proxy | Prediction |
|:--|:--|:--|
| **Commitment problem (CP)** | Weak institutions (V-Dem PCA index) | Less likely to ever sign |
| **Information asymmetry (IA)** | Prior fighting experience (UCDP Dyadic, δ = 0.95) | Sign earlier when resolved |

**H1** — CP-dominant conflicts less likely to sign → cross-sectional logit (N = 201)  
**H2** — IA-dominant conflicts sign earlier → discrete-time ClogLog hazard model on conflict-month spell  
**H3** — Larger ATT for IA-dominant conflicts → separate C&SA event studies by quadrant  

---

## Repository Structure

```
agreements_violence/
│
├── data/
│   ├── input/                      # UCDP, PA-X, V-Dem, World Bank, CEPII, UN
│   └── output/
│       ├── conflict_level/         # conflict_panel.csv (and quarterly/semester)
│       └── country_level/          # country_panel.csv
│
├── src/
│   ├── 1_data_generation/          # Panel construction notebooks + codebooks
│   ├── 2_data_analysis/            # EDA and descriptive statistics
│   ├── 3_0_csdid/                  # Main estimator (Callaway–Sant'Anna)
│   └── 5_survival_analysis/        # Bargaining proxies, hazard model
│
├── reports/                        # Research notes and drafts
├── pyproject.toml
└── README.md
```
<!-- 
---

## Data Sources

| Source | Coverage | Key variables |
|:--|:--|:--|
| UCDP/PRIO Conflict v25.1 | 1946–2024 | `conflict_id`, incompatibility, type |
| UCDP GED v25.1 | 1989–2024 | Fatalities (`best`), events, location |
| UCDP Dyadic v25.1 | 1946–2024 | Dyad-level conflict; experience construction |
| PA-X v9 | 1990–2023 | Agreement content, stage, type (71 conflicts) |
| V-Dem v16 | 1789–2024 | Institutional quality; CP proxies |
| World Bank GDP pc | 1960–2024 | GDP per capita |
| CEPII GeoDist | — | Bilateral distances and trade |
| UN GA Voting | 1946–2024 | UNGA roll-call alignment with UNSC members | -->
