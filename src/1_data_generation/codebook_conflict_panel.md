# Conflict Panel Codebook

**Dataset:** `data/output/conflict_level/conflict_panel.csv`  
**Unit:** conflict × month (`conflict_id`, `year_mo`)  
**Scope:** 201 state-based conflicts, January 1989 – December 2024 (86,832 rows)  
**Source:** `src/1_data_generation/conflict_panel.ipynb`  
**Technical notes:** `reports/conflict_panel_construction.tex`

---

## 1. Identifiers and time

| Variable | Meaning | Notes |
|---|---|---|
| `conflict_id` | UCDP conflict identifier | Primary panel id |
| `year_mo` | Month (YYYY-MM-DD, first of month) | Monthly timestamp |
| `year` | Calendar year | Derived from `year_mo` |
| `year_mo_numeric` | Month index (1 = January 1989) | Used for treatment date variables |
| `isocode` | ISO3 of dominant country | Conflict location with most fatalities |
| `country` | Dominant country name | |
| `region` | Region | |
| `isocode_num` | Numeric country code | Categorical code of `isocode` |
| `region_num` | Numeric region code | Categorical code of `region` |
| `isocode_array` | All ISO3 codes involved | Conflicts may span multiple countries |
| `countries_array` | All country names involved | Parallel to `isocode_array` |

---

## 2. Conflict intensity (UCDP GED)

| Variable | Meaning | Notes |
|---|---|---|
| `best` | Monthly fatalities (best estimate) | Sum across all GED events; 0 in dormancy months |
| `log_best` | log(1 + best) | |
| `n_events` | Number of GED events recorded | Monthly count |
| `n_isocode` | Number of countries involved this month | |
| `n_factions` | Number of armed factions (dyads) | Derived from `dyad_id` |
| `type_of_violence` | UCDP violence type | Always 1 (state-based) in this panel |
| `dyad_id` | Array of dyad identifiers | |
| `ged_event_month` | 1 if UCDP GED recorded ≥1 event this month | 0 in dormancy / pre-onset / post-conflict months |

---

## 3. Agreement indicators — any month (PA-X)

Equals 1 if a PA-X agreement of the given type was signed in that conflict-month, **regardless of whether UCDP recorded active violence**. Captures agreements during ceasefires and inter-episode pauses. Used for the survival / selection analysis.

| Variable | Meaning |
|---|---|
| `agreement` | Any PA-X agreement |
| `comp_agreement` | Comprehensive agreement (stage = SubComp) |
| `subs_agreement` | Substantive agreement (stage = SubPar) |
| `cea_agreement` | Ceasefire agreement (stage = CEA) |
| `cea_ceamix_agreement` | CEA mixed subtype (stagesub = CeaMix) |
| `cea_ceas_agreement` | CEA ceasefire subtype (stagesub = Ceas) |
| `cea_rel_agreement` | CEA related subtype (stagesub = Rel) |
| `ce` | Ceasefire mentions count (PA-X `ce` field) |

Under the `agreement` definition: **104 of 201 conflicts** ever sign at least one agreement (1,271 agreement-months).

---

## 4. Agreement indicators — GED-event month only (PA-X × UCDP)

Equals 1 only if *both* a PA-X agreement was signed **and** `ged_event_month = 1` (i.e., UCDP recorded at least one episode that month). Used as the treatment indicator in the CSDID causal analysis; agreements in dormancy months are excluded because there is no violence to reduce.

| Variable | Meaning |
|---|---|
| `agreement_ged` | Any PA-X agreement in an active-violence month |
| `comp_agreement_ged` | Comprehensive agreement in active-violence month |
| `subs_agreement_ged` | Substantive agreement in active-violence month |
| `cea_agreement_ged` | Ceasefire agreement in active-violence month |
| `cea_ceamix_agreement_ged` | CEA mixed in active-violence month |
| `cea_ceas_agreement_ged` | CEA ceasefire in active-violence month |
| `cea_rel_agreement_ged` | CEA related in active-violence month |

Under the `agreement_ged` definition: **71 of 201 conflicts** ever sign at least one agreement (746 agreement-months). The difference from `agreement` (33 conflicts) signed exclusively during dormancy periods or after their last GED event.

---

## 5. PA-X provision content tags

Binary monthly maxima of 63 PA-X content tags. Indicate whether any agreement signed in that conflict-month included a given provision. Used for heterogeneous treatment effects analysis.

`hriimon`, `ime`, `ddrprog`, `imun`, `tjrep`, `ppsaut`, `tjmis`, `protgrp`, `ppsvet`, `hriibod`,
`tpsloc`, `terps`, `pol`, `epsres`, `impk`, `epsoth`, `polnewtemp`, `protciv`, `hrtrinc`, `ssrddr`,
`ceprov`, `ppsint`, `ddrdemil`, `polpar`, `polps`, `hrbor`, `hrdem`, `medlog`, `tjvet`, `medsubs`,
`epsfis`, `tpssub`, `tpsoth`, `eleccomm`, `eps`, `ssrpol`, `medgov`, `imref`, `tpsaut`, `med`,
`hrii`, `cegen`, `ssrgua`, `ssrarm`, `tjcou`, `ppsoro`, `tjamban`, `tjvic`, `tjmech`, `polnewind`,
`mpsme`, `mpsjt`, `imoth`, `ppsothpr`, `ppsex`, `hrmob`, `ele`, `hrni`, `civso`, `pubad`,
`juscr`, `mps`, `prot`, `mpspro`

---

## 6. Conflict timeline and duration

| Variable | Meaning | Notes |
|---|---|---|
| `start_date` | First month with any GED event | Conflict onset |
| `ged_end_date` | Last month with any GED event | |
| `end_date` | Same as `ged_end_date` | No extension for post-GED agreements |
| `pax_first_date` | Month of first PA-X agreement (any type) | Reference only |
| `start_date_numeric` | `start_date` as month index | Same scale as `year_mo_numeric` |
| `end_date_numeric` | `end_date` as month index | |
| `duration_months` | Total calendar duration (months) | `end_date_numeric` − `start_date_numeric` |
| `active_duration_months` | Months with `ged_event_month = 1` | |
| `conflict_age` | Months elapsed since `start_date` | 0 in onset month; NaN before onset |
| `active_conflict_age` | Cumulative count of GED-event months | 0 in first active month |
| `start_year` | Calendar year of onset | |
| `current_month` | Calendar month (1–12) | |

---

## 7. Treatment variables

Two parallel sets of treatment variables, one for each agreement definition. The `_ged` variants are for CSDID; the plain variants are for survival analysis.

| Variable | Meaning | Use |
|---|---|---|
| `ever_agreement` | 1 if conflict ever signed any agreement | Survival |
| `ever_agreement_ged` | 1 if conflict ever signed during a GED-event month | CSDID |
| `first_agreement_date` | Month index of first agreement (0 = never) | Survival |
| `first_agreement_ged_date` | Month index of first agreement in GED-event month (0 = never) | CSDID |

The same pattern applies for `comp_agreement`, `subs_agreement`, `cea_agreement`, `cea_ceamix_agreement`, `cea_ceas_agreement`, `cea_rel_agreement`:  
→ `ever_{type}`, `ever_{type}_ged`, `first_{type}_date`, `first_{type}_ged_date`

---

## 8. Macro controls

| Variable | Meaning |
|---|---|
| `gdp_pc_current_usd` | GDP per capita (current USD, World Bank) |
| `gdp_current_usd` | GDP (current USD, World Bank) |
| `log_gdp_pc_current_usd` | log GDP per capita |
