# Agreements and Violence — Project Reference

## Research context

Academic paper targeting an economics journal. The paper has two parts:

1. **Causal effect of peace agreements on violence** — does signing a first agreement reduce conflict fatalities?
2. **Bargaining model** — why do so few conflicts reach agreements? Framed through Fearon (1995): information asymmetries vs. commitment problems.

**Team:** PIs: Laura Mayoral, Hannes Müller, Dominic Rohner, Christopher Rauh. RA: Lucia Sauer.

---

## Repository structure

```
agreements_violence/
├── data/
│   ├── input/           # Raw sources: ucdp/, pax/, v_dem/, un/, distance/, gdp_pc/
│   └── output/
│       ├── conflict_level/   # conflict_panel.csv, conflict_panel_quarters.csv, conflict_panel_semesters.csv
│       └── country_level/    # country_panel.csv
├── src/
│   ├── 1_data_generation/    # Panel construction notebooks + codebooks
│   ├── 2_data_analysis/      # EDA, descriptive stats
│   ├── 3_causal_effect_estimation/
│   │   ├── 3_0_csdid/        # Callaway-Sant'Anna DiD (main estimator)
│   │   ├── 3_1_sdid/         # Synthetic DiD (robustness)
│   │   ├── 3_2_event_study/  # Event-study windows
│   │   └── 3_3_iv/           # IV / 2SLS
│   ├── 4_results/            # Figures and output tables
│   └── 5_structural_model/   # Bargaining proxies, hazard models, logit
└── reports/
```

---

## Data panels

### Conflict panel — `data/output/conflict_level/conflict_panel.csv`
- **Unit:** conflict × month (`conflict_id`, `year_mo`)
- **Built in:** [src/1_data_generation/conflict_panel.ipynb](src/1_data_generation/conflict_panel.ipynb)
- **Codebook:** [src/1_data_generation/codebook_conflict_panel.md](src/1_data_generation/codebook_conflict_panel.md)
- **Key variables:**
  - `best` — monthly fatalities (best estimate, UCDP)
  - `n_events` — monthly event count
  - `agreement` — any PA-X agreement this month
  - `first_agreement_date` — month index of first agreement (0 = never)
  - `ever_agreement` — 1 if conflict ever signs any agreement
  - `ceasfire_agreements_mentions` — **primary treatment variable** (ceasefire agreements/mentions)
- **Sample:** 201 conflicts, ~86,832 conflict-month observations

Quarterly and semester aggregations also available:
- `conflict_panel_quarters.csv` — used for CSDID; defines `first_agreement` (treated = active conflicts above activity threshold)
- `conflict_panel_semesters.csv`

### Country panel — `data/output/country_level/country_panel.csv`
- **Unit:** country × month (`isocode`, `year_mo`)
- **Built in:** [src/1_data_generation/country_panel.ipynb](src/1_data_generation/country_panel.ipynb)
- **Codebook:** [src/1_data_generation/codebook_country_panel.md](src/1_data_generation/codebook_country_panel.md)
- **Additional variables not in conflict panel:**
  - Instruments (IVs) for 2SLS — see IV section below
  - Country-level aggregation of agreement types and counts

> **Level-of-analysis note:** The conflict panel is at conflict_id × month; the country panel is at isocode × month. When merging country-level variables (V-Dem, GDP, IV instruments) into the conflict panel, you must join on `isocode × year` (or `year_mo`), not on `conflict_id`. Some conflicts span multiple countries (`isocode_array`).

---

## Treatment definition

The primary treatment is the **first peace agreement** for each conflict (`first_agreement`).

- In the CSDID analysis: "treated" conflicts must pass an **activity threshold** of ≥12 deaths in the two quarters before treatment. Low-activity treated units are reclassified as untreated.
- `gvar` = quarter of first agreement (Callaway-Sant'Anna group variable); 0 = never treated.
- Studying sequences of subsequent agreements is a potential extension once results on the first agreement are solid, but is **not the current focus**.

> **Note:** Earlier versions of the project used `ceasfire_agreements_mentions` as the primary treatment and built a matching-based event-study design (`src/3_causal_effect_estimation/3_2_event_study/`). That approach has been **abandoned**. Do not reference it or suggest resuming it. The canonical analysis is CSDID on `first_agreement`.

---

## Causal effect estimation

### CSDID (main) — `src/3_causal_effect_estimation/3_0_csdid/`

Key file: [src/3_causal_effect_estimation/3_0_csdid/first_agreement_active_csdid_quarterly.do](src/3_causal_effect_estimation/3_0_csdid/first_agreement_active_csdid_quarterly.do)

- Collapses monthly conflict panel to **quarterly** frequency
- Activity threshold filters low-intensity treated units
- Control units also filtered: dropped if inactive (deaths_prev2q < 12) in control periods
- Trims to UCDP conflict window (start_yq to end_yq)
- Runs `csdid2` with `notyet` comparison group, `drimp` estimator
- Event window: ±8 quarters
- Outcome: `ln_deaths = ln(best + 1)`

**Main ATT results (quarterly, drimp):** coefficient ≈ −0.69 (se ≈ 0.22, p = 0.002)

Results figures: [src/4_results/csdid/](src/4_results/csdid/)

### IV / 2SLS — `src/3_causal_effect_estimation/3_3_iv/`

Three instrument sets (all built in `country_panel.ipynb`):
1. **Regional agreement spillovers** — agreement intensity in same region/subregion, excluding own country, weighted by trade share or inverse distance (`agree_region_excl_w_trade`, `agree_subreg_excl_w_dist`, etc.)
2. **UN SC voting similarity** — UNGA roll-call alignment with SC members (`influence`, `influence_gdp`, `influence_veto`)
3. **SC external support** — SC members' conflict involvement outside focal country (`sc_at_war_outside_isocode`, etc.)

Results: [src/4_results/iv_regressions/](src/4_results/iv_regressions/)

---

## Bargaining model (Section 5) — current active work

**Objective:** Explain *why* 135 of 201 conflicts never reach an agreement, using Fearon (1995) bargaining theory.

Framework: conflicts are classified along two friction dimensions:
- **Information asymmetries (IA):** parties lack knowledge of each other's strength/resolve; fighting resolves this
- **Commitment problems (CP):** parties cannot credibly commit to honoring agreements; fighting makes this worse

### Hypotheses

| # | Question | Method |
|---|---|---|
| H1 | CP-dominant conflicts less likely to sign | Cross-sectional logit (N=201) |
| H2 | IA-dominant conflicts sign earlier | Discrete-time ClogLog hazard model on conflict-month spell |
| H3 | Larger/more persistent ATT for IA-dominant conflicts | Separate CS event studies by conflict type |
| H4 | Provision quality matters more for CP conflicts | Interact treatment with PA-X provisions index |

**Currently working on H1 and H2.** H3 and H4 are next steps.

### Key notebook — [src/5_structural_model/bargaining_model_hr.ipynb](src/5_structural_model/bargaining_model_hr.ipynb)

Workflow:
1. Load `conflict_panel.csv` and `conflict_panel_quarters.csv`
2. Merge proxies: UCDP incompatibility, number of factions, termination type, experience, V-Dem variables
3. Build spell dataset (`pre_treatment`): conflict-month observations up to first agreement, used for hazard model
4. Construct time-varying features: `log_conflict_age`, `log_cum_deaths`, `within_conflict_learning`, `log_recent_intensity`, `combat_volatility`, `multiple_conflicts_binary`
5. Run ClogLog hazard model (`run_hazard`) for H2
6. Build PCA-based indices at conflict level: `commit_index` (CP), `info_index` (IA)
7. Classify conflicts into 4 quadrants: High/Low IA × High/Low CP
8. Run logit (`run_logit`) for H1

### Proxy construction — [src/5_structural_model/proxy_definitions.md](src/5_structural_model/proxy_definitions.md)

**Commitment problem proxies** (inverted so high = more CP):
- `vdem_state_territorial_control` (`v2svstterr`) → `weak_state_preconflict`
- `vdem_horizontal_accountability` (`v2x_horacc`) → `weak_accountability_preconflict`
- `vdem_judicial_constraints` (`v2x_jucon`) → `weak_judicial_preconflict`
- `vdem_legislative_constraints` (`v2xlg_legcon`) → `weak_legislative_preconflict`
- `vdem_wb_political_stability` → `weak_political_stability_preconflict`
- `vdem_neopatrimonial` (`v2x_neopat`) — use directly (higher = more CP)

**Information asymmetry proxies** (higher = more IA):
- `experience_total` / `exp_direct` — past fighting between same parties (via UCDP Dyadic, discounted at δ=0.95)
- `within_conflict_learning` — time-varying: discounted cumulative `n_events` within conflict
- `log_recent_intensity` — rolling 6-month mean of `n_events`
- `combat_volatility` — rolling 12-month std of `n_events`
- `multiple_conflicts_binary` — concurrent conflicts in same country

All `_pre5y` suffix versions are 5-year pre-conflict rolling means for use as pre-treatment proxies.

**Index construction:**
- `commit_index` — PCA(1) on inverted CP variables, rescaled [0,1]
- `info_index` — inverse IHS-transformed `experience_total`, rescaled [0,1]
- `commit_relative` / `ia_relative` — share of each index in combined score

### Helper functions — `src/5_structural_model/functions/`

| File | Purpose |
|---|---|
| `build_vdem_variables.py` | Load V-Dem, compute 5-year rolling means, merge to panel via COW code |
| `build_experience.py` | Compute discounted experience score from UCDP Dyadic |
| `build_experience_compound.py` | Extended experience: direct + government-shared experience |
| `build_number_factions.py` | Count armed factions per conflict-year from UCDP Dyadic |
| `build_conflict_termination.py` | Merge UCDP termination outcomes |
| `hazard_model.py` | Run ClogLog discrete-time hazard with clustered SE, print HR table |
| `run_logit.py` | Run logit with robust SE, print OR table |
| `plot_bargaining_space.py` | 2D scatter of IA vs. CP indices by agreement outcome |

---

## Input data sources

| Source | File | Key variables |
|---|---|---|
| UCDP/PRIO Conflict v25.1 | `data/input/ucdp/UcdpPrioConflict_v25_1.csv` | `conflict_id`, `incompatibility`, `type_of_conflict` |
| UCDP GED v25.1 | `data/input/ucdp/GEDEvent_v25_1.csv` | Events, fatalities, locations |
| UCDP Dyadic v25.1 | `data/input/ucdp/Dyadic_v25_1.csv` | Dyad-level conflict, experience construction |
| UCDP Conflict Termination v4 | `data/input/ucdp/UCDPConflictTerminationDataset_v4_2024_Conflict.csv` | Termination type |
| PA-X v9 | `data/input/pax/pax_data_2144_agreements_v9_10.csv` | Agreement content, stage, type |
| V-Dem v16 | `data/input/v_dem/V-Dem-CY-Full+Others-v16.csv` | Institutional quality, regime type |
| V-Dem codebook | `data/input/v_dem/codebook.pdf` | Variable definitions |
| PA-X codebook | `data/input/pax/PA_X_codebook_v9.pdf` | Agreement content tag definitions |
| World Bank GDP | `data/input/gdp_pc/gdp_pc.csv` | GDP per capita |
| CEPII GeoDist | `data/input/distance/dist_cepii.xls` | Bilateral distances |
| UN GA voting | `data/input/un/2025_9_19_ga_voting.csv` | UNGA roll-call votes |
| SC membership | `data/input/un/DPPA-SCMembership.csv` | UNSC membership by year |

---

## Key variable cross-reference

| Variable | Panel | Meaning |
|---|---|---|
| `best` | conflict, country | Fatalities best estimate (monthly) |
| `ln_deaths` | quarterly (Stata) | `ln(best + 1)` at quarterly level |
| `agreement` | both | Any PA-X agreement this month |
| `first_agreement` | quarterly | =1 in first active-agreement quarter (CSDID treatment indicator) |
| `first_agreement_quarter` | quarterly | yq of first agreement (. if untreated/inactive) |
| `gvar` | quarterly | CS group variable (0 = never treated) |
| `ceasfire_agreements_mentions` | both | Primary treatment for event study and IV |
| `ever_agreement` | both | 1 if conflict/country ever signs |
| `commit_index` | conflict-level | PCA commitment problem score [0,1] |
| `info_index` | conflict-level | IA score (inverse experience) [0,1] |
| `experience_total` | conflict-level | Discounted prior fighting score (UCDP Dyadic, δ=0.95) |
| `vdem_*_pre5y` | conflict-level | 5-year pre-conflict rolling mean of V-Dem variable |

---

## Environment

- Python 3.12, managed with `uv` (`.venv/`)
- Stata 17 for CSDID (`csdid2` package)
- Key Python packages: pandas, numpy, statsmodels, lifelines, sklearn, matplotlib, seaborn
