# Conflict Panel Codebook

**Dataset:** `conflict_panel.csv`  
**Unit:** conflict-month  
**Scope:** conflict intensity + agreements + PA-X content/metadata + timing + controls  
**Source notebook:** `src/1_data_generation/conflict_panel.ipynb`

---

## 1) Identifiers and time
| Variable | Meaning | Notes |
| --- | --- | --- |
| `conflict_id` | UCDP conflict id | Primary panel id |
| `year_mo` | Month (YYYY-MM) | Monthly timestamp |
| `year` | Calendar year | Derived from `year_mo` |
| `year_mo_numeric` | Month index | 1 = first month in panel |
| `isocode` | Main country ISO3 | Conflict location |
| `country` | Country name | From ISO metadata |
| `region` | region | |
| `isocode_num` | Numeric id | Categorical codes |
| `region_num` | Numeric region id | Categorical codes |
| `isocode_array` | ISO3 list for conflict | Multiple countries possible |
| `countries_array` | Country names list | Parallel to `isocode_array` |

---

## 2) Conflict intensity (UCDP)
| Variable | Meaning | Notes |
| --- | --- | --- |
| `best` | Fatalities (best estimate) | Monthly |
| `log_best` | log(1 + best) | |
| `n_events` | Number of events | Monthly |
| `n_isocode` | Number of countries in conflict | |
| `type_of_violence` | UCDP conflict type | |
| `any_violence` | 1 if `log_best` > 0 | Binary |
| `since_any_violence` | Months since last violence | Within conflict |
| `conflict_active` | Active conflict indicator | Based on recency |

---

## 3) Agreement occurrence (PA-X, monthly)
| Variable | Meaning |
| --- | --- |
| `agreement` | Any agreement this month |
| `comp_agreement` | Comprehensive agreement |
| `subs_agreement` | Substantive agreement |
| `cea_agreement` | Ceasefire-related agreement |
| `cea_ceamix_agreement` | CEA mixed subtype |
| `cea_ceas_agreement` | CEA ceasefire subtype |
| `cea_rel_agreement` | CEA related subtype |
| `ce` | Ceasefire mentions count |

---

## 4) Agreement content indicators (PA-X tags)
Binary monthly maxima of PA-X content tags (agreement heterogeneity).

Variables:  
`hriimon`, `ime`, `ddrprog`, `imun`, `tjrep`, `ppsaut`, `tjmis`, `protgrp`, `ppsvet`, `hriibod`,  
`tpsloc`, `terps`, `pol`, `epsres`, `impk`, `epsoth`, `polnewtemp`, `protciv`, `hrtrinc`, `ssrddr`,  
`ceprov`, `ppsint`, `ddrdemil`, `polpar`, `polps`, `hrbor`, `hrdem`, `medlog`, `tjvet`, `medsubs`,  
`epsfis`, `tpssub`, `tpsoth`, `eleccomm`, `eps`, `ssrpol`, `medgov`, `imref`, `tpsaut`, `med`,  
`hrii`, `cegen`, `ssrgua`, `ssrarm`, `tjcou`, `ppsoro`, `tjamban`, `tjvic`, `tjmech`, `polnewind`,  
`mpsme`, `mpsjt`, `imoth`, `ppsothpr`, `ppsex`, `hrmob`, `ele`, `hrni`, `civso`, `pubad`,  
`juscr`, `mps`, `prot`, `mpspro`

---

## 5) PA-X agreement metadata (raw fields kept)
These are PA-X agreement-level fields carried into the panel for reference.  
Variables include (verbatim):  
`con`, `contp`, `pp`, `ppname`, `reg`, `agtid`, `ver`, `agt`, `dat`, `status`, `lgt`, `n_characters`, `agtp`, `stage`, `stagesub`, `part`, `thrdpart`, `othagr`, `loc2iso`, `loc1gwno`, `loc2gwno`, `ucdpagr`, `pamagr`, `cowwar`, `interim`, `stdef`, `stgen`, `stcon`, `stsd`, `stref`, `stsym`, `stind`, `stuni`, `stbor`, `stxbor`, `polgen`, `polpartrans`, `polparoth`, `tral`, `congen`, `conren`, `cons`, `ppsge`, `ppsge:st`, `ppsge:sub`, `ppsex:st`, `ppsex:sub`, `ppsoro:st`, `ppsoro:sub`, `ppsothpr:st`, `ppsothpr:sub`, `ppsvet:st`, `ppsvet:sub`, `ppsaut:st`, `ppsaut:sub`, `ppsint:st`, `ppsint:sub`, `ppsoth`, `ppsoth:st`, `ppsoth:sub`, `mpsoth`, `hrgen`, `hrcp`, `cprlife`, `cprtort`, `cpreq`, `cprslav`, `cprlib`, `cprdet`, `cprfmov`, `cprfspe`, `cprfass`, `cprtria`, `cprpriv`, `cprvote`, `cprreli`, `cproth`, `hrsec`, `serprop`, `serwork`, `serheal`, `seredu`, `serstdl`, `sershel`, `serss`, `sercult`, `seroth`, `hrcit`, `citgen`, `citrights`, `citdef`, `citoth`, `hrdet`, `medoth`, `prototh`, `rioth`, `hrnime`, `hrnine`, `hrnioth`, `hriioth`, `juscrsp`, `juscrsys`, `juscrpow`, `jusem`, `jusju`, `juspri`, `justra`, `dev`, `devsoc`, `devhum`, `devinfra`, `nec`, `natres`, `intfu`, `bus`, `tax`, `taxpo`, `taxref`, `taxoth`, `ban`, `cenban`, `banpers`, `banint`, `banxb`, `laref`, `larefman`, `larefret`, `larefoth`, `lanom`, `lach`, `lachta`, `lachit`, `lachpro`, `lachoth`, `laen`, `wat`, `ssrint`, `ssrpsf`, `ssrff`, `cor`, `ssrcrocr`, `ssrdrugs`, `terr`, `tjgen`, `tjam`, `tjampro`, `tjsan`, `tjpower`, `tjjanc`, `tjjaic`, `tjprire`, `tjrsym`, `tjrma`, `tjnr`, `imsrc`

---

## 6) Conflict timeline and duration
| Variable | Meaning |
| --- | --- |
| `start_date`, `end_date` | Conflict start/end dates |
| `start_date_numeric`, `end_date_numeric` | Numeric month indices |
| `duration_months` | Total conflict duration (months) |
| `active_duration_months` | Duration while active |
| `conflict_age` | Months since conflict start |
| `conflict_age_less_6m` | Age < 6 months |
| `conflict_age_less_12m` | Age < 12 months |
| `conflict_age_less_18m` | Age < 18 months |
| `conflict_age_less_24m` | Age < 24 months |
| `conflict_age_less_30m` | Age < 30 months |
| `active_conflict_age` | Age while active |
| `start_year` | Start year |
| `current_month` | Month index within conflict |

---

## 7) Treatment timing variables
**First treatment month (numeric) and ever‑treated indicators by agreement type.**

| Variable pattern | Meaning |
| --- | --- |
| `first_*_date` | Month index of first occurrence (0 = never) |
| `treated_*` | 1 if conflict ever experiences the agreement type |

Agreement types: `agreement`, `comp_agreement`, `subs_agreement`, `cea_agreement`, `cea_ceas_agreement`, `cea_ceamix_agreement`, `cea_rel_agreement`.

Additional timing:
- `since_last_agreement` = months since last agreement
- `sequence_12m` = agreement sequence indicator (12-month window)

---

## 8) Ceasefire dynamics and "no‑ceasefire" flags
| Variable | Meaning |
| --- | --- |
| `ceasefire_mentions` | Ceasefire mentions indicator |
| `treated_ceasfire_mentions` | Ever had ceasefire mentions |
| `ceasfire_agreements_mentions` | Ceasefire agreements/mentions indicator |
| `treated_ceasfire_agreements_mentions` | Ever had ceasefire agreements/mentions |
| `until_ce_mentions` | Months until next ceasefire mention |
| `ce_mentions_active` | Active if `until_ce_mentions` >= 6 |
| `until_cea_agreement` | Months until next CEA agreement |
| `cea_agreement_active` | Active if `until_cea_agreement` >= 6 |
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

## 9) Macro controls and flags
| Variable | Meaning |
| --- | --- |
| `gdp_pc_current_usd` | GDP per capita (current USD) |
| `gdp_current_usd` | GDP (current USD) |
| `log_gdp_pc_current_usd` | log GDP per capita |
| `real_observation` | 1 for real data, 0 for padded rows |

