# Country Panel Codebook

**Dataset:** `country_panel.csv`  
**Unit:** country–month  
**Scope:** conflict + agreements + instruments + covariates  
**Source notebook:** `src/1_data_generation/country_panel.ipynb`

---

## 1) Identifiers and time
| Variable | Meaning | Notes |
| --- | --- | --- |
| `isocode` | Country ISO3 code | Primary panel id |
| `country` | Country name | From ISO metadata |
| `year_mo` | Month (YYYY-MM) | Monthly timestamp |
| `year` | Calendar year | Derived from `year_mo` |
| `year_mo_numeric` | Month index | 1 = first month in panel |
| `region` |  region | |
| `subregion` |  subregion | |
| `isocode_num` | Numeric country id | Categorical codes |
| `region_num` | Numeric region id | Categorical codes |

---

## 2) Conflict intensity (UCDP)
| Variable | Meaning | Notes |
| --- | --- | --- |
| `best` | Fatalities (best estimate) | Monthly, country-level |
| `log_best` | log(1 + best) | |
| `n_events` | Number of conflict events | Monthly |
| `n_conflicts` | Number of active conflicts | Monthly |
| `any_violence` | 1 if `log_best` > 0 | Binary |
| `since_any_violence` | Months since last violence | Within country |
| `conflict_active` | Active conflict indicator | 24‑month rule (12 months for ≤1990) |

---

## 3) Agreement occurrence (PA‑X)
| Variable | Meaning | Notes |
| --- | --- | --- |
| `agreement` | Any agreement this month | Binary |
| `comp_agreement` | Comprehensive agreement | Binary |
| `subs_agreement` | Substantive agreement | Binary |
| `cea_agreement` | Ceasefire-related agreement | Binary |
| `cea_ceamix_agreement` | CEA mixed subtype | Binary |
| `cea_ceas_agreement` | CEA ceasefire subtype | Binary |
| `cea_rel_agreement` | CEA related subtype | Binary |
| `ce` | Ceasefire mentions count | Integer |
| `agreement_count` | # agreements this month | |
| `comp_agreement_count` | # comprehensive | |
| `subs_agreement_count` | # substantive | |
| `cea_agreement_count` | # CEA | |
| `cea_ceamix_agreement_count` | # CEA mix | |
| `cea_ceas_agreement_count` | # CEA ceasefire | |
| `cea_rel_agreement_count` | # CEA related | |
| `ce_count` | # ceasefire mentions | |

---

## 4) Agreement content indicators (PA‑X features)
**Binary monthly maxima of PA‑X content tags (agreement heterogeneity).**  
Variables:  
`hriimon`, `ime`, `ddrprog`, `imun`, `tjrep`, `ppsaut`, `tjmis`, `protgrp`, `ppsvet`, `hriibod`,  
`tpsloc`, `terps`, `pol`, `epsres`, `impk`, `epsoth`, `polnewtemp`, `protciv`, `hrtrinc`, `ssrddr`,  
`ceprov`, `ppsint`, `ddrdemil`, `polpar`, `polps`, `hrbor`, `hrdem`, `medlog`, `tjvet`, `medsubs`,  
`epsfis`, `tpssub`, `tpsoth`, `eleccomm`, `eps`, `ssrpol`, `medgov`, `imref`, `tpsaut`, `med`,  
`hrii`, `cegen`, `ssrgua`, `ssrarm`, `tjcou`, `ppsoro`, `tjamban`, `tjvic`, `tjmech`, `polnewind`,  
`mpsme`, `mpsjt`, `imoth`, `ppsothpr`, `ppsex`, `hrmob`, `ele`, `hrni`, `civso`, `pubad`,  
`juscr`, `mps`, `prot`, `mpspro`

**Interpretation:** each variable = 1 if the corresponding PA‑X content category appears in any agreement that month for the country.

---

## 5) Instrument sets (IVs)
**Set 1: Regional agreement spillovers (excluding own)**
| Variable | Meaning | Construction |
| --- | --- | --- |
| `agree_region_excl_w_trade` | Region agreement intensity × trade share | Regional agreements (excl. own) * share of exports to region |
| `agree_subreg_excl_w_trade` | Subregion agreement intensity × trade share | Subregional agreements (excl. own) * share of exports to subregion |
| `agree_region_excl_w_dist` | Region agreement intensity × inverse distance | Regional agreements (excl. own) * inverse avg regional distance |
| `agree_subreg_excl_w_dist` | Subregion agreement intensity × inverse distance | Subregional agreements (excl. own) * inverse avg subregional distance |

**Set 2: UN Security Council voting influence**
| Variable | Meaning | Construction |
| --- | --- | --- |
| `influence` | Raw SC voting similarity | Σ same_vote with SC members |
| `influence_gdp` | GDP‑weighted SC influence | Σ same_vote × GDP weight |
| `influence_log_gdp` | Log‑GDP‑weighted SC influence | Σ same_vote × log‑GDP weight |
| `influence_veto` | Veto‑weighted SC influence | Σ same_vote × veto factor (P5=10, others=1) |

**Set 3: SC members’ external support elsewhere**
| Variable | Meaning | Construction |
| --- | --- | --- |
| `sc_at_war_outside_isocode` | SC support outside country | (total SC involvement − in‑country) / total |
| `sc_at_war_outside_sub_region` | SC support outside subregion | (total − subregion) / total |
| `sc_at_war_outside_region` | SC support outside region | (total − region) / total |

---

## 6) Treatment timing variables
**First treatment month (numeric) and ever‑treated indicators by agreement type.**

| Variable pattern | Meaning |
| --- | --- |
| `first_*_date` | Month index of first occurrence (0 = never) |
| `treated_*` | 1 if the country ever experiences the agreement type |

Agreement types: `agreement`, `comp_agreement`, `subs_agreement`, `cea_agreement`, `cea_ceas_agreement`, `cea_ceamix_agreement`, `cea_rel_agreement`.

---

## 7) Ceasefire dynamics & “no‑ceasefire” flags
| Variable | Meaning |
| --- | --- |
| `ceasefire_mentions` | Ceasefire mentions indicator |
| `treated_ceasfire_mentions` | Ever had ceasefire mentions |
| `ceasfire_agreements_mentions` | Ceasefire agreements/mentions indicator |
| `treated_ceasfire_agreements_mentions` | Ever had ceasefire agreements/mentions |
| `until_ce_mentions` | Months until next ceasefire mention |
| `ce_mentions_active` | Active if `until_ce_mentions` ≥ 6 |
| `until_cea_agreement` | Months until next CEA agreement |
| `cea_agreement_active` | Active if `until_cea_agreement` ≥ 6 |
| `agreement_no_ceasefire` | Agreement with no ceasefire mention |
| `treated_agreements_no_ceasefire` | Ever had agreement w/o ceasefire |
| `agreement_no_ceasefire_mentions_agreement_6m` | No‑ceasefire agreement & active 6m |
| `comp_agreement_no_ceasefire` | Comprehensive agreement w/o ceasefire |
| `treated_comp_agreements_no_ceasefire` | Ever had comp. w/o ceasefire |
| `comp_agreement_no_ceasefire_mentions_agreement_6m` | Comp. no‑ceasefire & active 6m |
| `subs_agreement_no_ceasefire` | Substantive agreement w/o ceasefire |
| `treated_subs_agreements_no_ceasefire` | Ever had subs. w/o ceasefire |
| `subs_agreement_no_ceasefire_mentions_agreement_6m` | Subst. no‑ceasefire & active 6m |

*Note: `ceasfire_agreements_mentions` is the treatment we are using for the analysis*
---

## 8) Macro controls
| Variable | Meaning |
| --- | --- |
| `gdp_pc_current_usd` | GDP per capita (current USD) |
| `gdp_current_usd` | GDP (current USD) |
| `log_gdp_pc_current_usd` | log GDP per capita |

---

## 9) Quality flags
| Variable | Meaning |
| --- | --- |
| `real_observation` | 1 for real data, 0 for padded rows | Useful if panel expanded |

