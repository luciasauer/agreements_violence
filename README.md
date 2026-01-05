<h1 align="center">Agreements and Violence</h1>


<p align="center">
  <b>Principal Investigators:</b> Laura Mayoral · Hannes Müller · Dominic Rohner · Christopher Rauh <br>
  <b>Research Assistant:</b> Lucia Sauer <br>

</p>
<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python" alt="Python Badge">
  <img src="https://img.shields.io/badge/Stata-17-blue" alt="Stata Badge">
  <img src="https://img.shields.io/badge/Pixi-virtual_env-orange" alt="Pixi Badge">
</p>

  
---

## Overview

This project constructs country-month and conflict-month panels combining conflict, peace agreement, and macroeconomic data to analyze the relationship between peace agreements and subsequent violence.

> **Research question:** How do peace agreements affect violence dynamics at the country-month and conflict-month levels?


## Repository Structure


```js
agreements_violence/
│
├── data/
│   ├── input/                      # Raw data sources
│   │   ├── distance/
│   │   ├── external_support/
│   │   ├── gdp_pc/
│   │   ├── isocodes/
│   │   ├── pax/
│   │   ├── trade/
│   │   ├── ucdp/
│   │   └── un/
│   └── output/                     # Final panels and derived datasets
│
├── src/
│   ├── 1_data_generation/          # Ingestion, harmonization, panel build
│   ├── 2_data_analysis/            # Descriptive analysis
│   ├── 3_causal_effect_estimation/
│   │   ├── 3_1_event_study/         # Event-study design and CSDID
│   │   └── 3_2_IV/                  # IV strategy and 2SLS
│   └── 4_results/                  # Tables, figures, results synthesis
│
├── reports/                        # Research notes and drafts
├── pyproject.toml
├── uv.lock
└── README.md
```
---

## Identification Strategy and Main Results

### **Treatment Definition**
Agreements are classified as **ceasefires** either by their **stage** or by explicit **ceasefire provisions**.

### **1) Event-Study (CSDID)**

We construct **36-month windows** centered on treatment at **t = 18** for treated units using the tool `window_generator.py` from the country and conflict panel datasets. Control windows are **clean of treatment** and randomly matched (up to **5 controls per treated window**). We estimate dynamic effects using **CSDID**, with wild bootstrap standard errors clustered at isocode.

**Specification (event-study):**
```math
y_{i,t} = \alpha_i + \lambda_t + \sum_{k \neq -1}\beta_k \cdot \mathbf{1}[t - T_i = k] + \varepsilon_{i,t}
```


#### Main Results - Conflict Level

<div style="display: flex; justify-content: center; gap: 20px;">

  <div style="text-align: center;">
    <img src="src/4_results/event_study/conflict_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_baseline.png" width="400">
    <p><em>Conflict Level - Baseline specification</em></p>
  </div>

  <div style="text-align: center;">
    <img src="src/4_results/event_study/conflict_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_control_y_pre6.png" width="400">
    <p><em>Conflict Level - Controlling pre treatment violence</em></p>
  </div>

  <div style="text-align: center;">
    <img src="src/4_results/event_study/conflict_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_baseline_quarterly.png" width="400">
    <p><em>Conflict Quarter Level Aggregation</em></p>
  </div>

</div>

**ATT Summary — Conflict Level**

| Estimator |Treated_w | Control_w| Coefficient | Std. Error |  p-value | 95% CI |
|:--|--:|--:|--:|--:|--:|:--|
| Monthly (baseline) | 99 | 495 | -0.46  | 0.25  |    0.071  |  [-0.976, 0.041]
| Monthly +  $\bar{Y}_{-6,-1}$ controls | 99 | 495 | -0.362  | 0.273   | 0.184   | [0.896, 0.172]
| Quarterly outcome | 99 | 495 | -0.687  | 0.218  |  0.002  |  [-1.115, -0.260]




#### Main Results - Country Level

<div style="display: flex; justify-content: center; gap: 20px;">

  <div style="text-align: center;">
    <img src="src/4_results/event_study/country_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_baseline.png" width="400">
    <p><em>Country Level - Baseline specification</em></p>
  </div>

  <div style="text-align: center;">
    <img src="src/4_results/event_study/country_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_control_y_pre6.png" width="400">
    <p><em>Country Level - Controlling pre treatment violence</em></p>
  </div>

  <div style="text-align: center;">
    <img src="src/4_results/event_study/country_level/random_matching/ceasfire_agreements_mentions/18_1/eventstudy_baseline_quarterly.png" width="400">
    <p><em>Country Quarter Level Aggregation</em></p>
  </div>

</div>

**ATT Summary — Country Level**

| Estimator |Treated_w | Control_w| Coefficient | Std. Error |  p-value | 95% CI |
|:--|--:|--:|--:|--:|--:|:--|
| Monthly (baseline) | 112 | 560 | -0.471  |  0.218  |     0.031  |  [-0.899, -0.043]
| Monthly +  $\bar{Y}_{-6,-1}$ controls | 112 | 560 | 0.456  |  0.221  |  0.039    | [-0.889, -0.024]
| Quarterly outcome | 112 | 560 | -0.402  | 0.220  |  0.068  |  [-0.834, 0.030]

 
   
### **2) Instrumental Variables (2SLS)**

#### 2.1 Agreements spillover (regional exposure)

Captures exogenous exposure to agreement activity in nearby or economically connected countries weighting by regional/subregional distance and trade intensity (CEPII GeoDist, BACI). Countries embedded in dense regional networks face stronger diplomatic and normative pressures to adopt similar agreement patterns, increasing ceasefire probability.

#### 2.2 UN voting similarity with UNSC
Measures political alignment with UN Security Council members through UNGA roll‑call voting similarity, where greater alignment with UNSC members increases access to mediation, monitoring, and diplomatic leverage, raising the likelihood of ceasefire agreements.

#### 2.3 External Support (UNSC involvement abroad)
Captures shifts in UNSC members’ conflict involvement outside the focal country/region. When UNSC members are engaged in other conflicts, their attention and capacity for mediation shift, affecting the probability of ceasefire agreements in the focal country.