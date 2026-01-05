# Instrument Sets Codebook

**Project:** agreements_violence country panel  
**Unit:** country-month (instruments merged by year where applicable)  
**Sources:** PA-X agreements, BACI trade, CEPII distance, UN voting similarity + UNSC membership + GDP, UCDP External Support

---

## Set 1. Regional peace agreement spillovers (excluding own)
**Concept:** past agreement activity in the same region/subregion, excluding the focal country, weighted by economic proximity or geographic proximity.

| Variable | Meaning | Notes |
| --- | --- | --- |
| `agree_region_excl_w_trade` | Region-level agreement intensity (excl. own) weighted by trade | `agreement_region_excl` = regional monthly sum of agreement counts minus own; trade share from BACI (1995–2023), country-level |
| `agree_subreg_excl_w_trade` | Subregion-level agreement intensity (excl. own) weighted by trade | Same logic, subregion weights |
| `agree_region_excl_w_dist` | Region-level agreement intensity (excl. own) weighted by inverse distance | Inverse of avg within-region distance (CEPII, 1000 km) |
| `agree_subreg_excl_w_dist` | Subregion-level agreement intensity (excl. own) weighted by inverse distance | Inverse of avg within-subregion distance (CEPII, 1000 km) |

**Construction (concise):**
- `agree_region_excl_w_trade` = `agreement_region_excl` * `percent_export_region_c`
- `agree_subreg_excl_w_trade` = `agreement_subregion_excl` * `percent_export_subregion_c`
- `agree_region_excl_w_dist` = `agreement_region_excl` * `inv_dist_region_c`
- `agree_subreg_excl_w_dist` = `agreement_subregion_excl` * `inv_dist_subregion_c`

**Weight details:**
- `percent_export_region_c` = share of a country’s exports going to partners in its region.  
- `percent_export_subregion_c` = share of exports to partners in its subregion.  
- `inv_dist_region_c`, `inv_dist_subregion_c` = inverse of the country’s average bilateral distance to other countries in its region/subregion.  
- Missing weights are filled with the global mean before multiplying.

---

## Set 2. UN Security Council voting influence
**Concept:** exposure to Security Council members’ voting positions in the UN, weighted by their power.

| Variable | Meaning | Notes |
| --- | --- | --- |
| `influence` | Raw SC voting similarity | Country-year; merged to months by year; missing set to 0 |
| `influence_gdp` | GDP-weighted SC influence | GDP weights for SC members, missing GDP treated as 0 |
| `influence_log_gdp` | Log-GDP-weighted SC influence | Alternative GDP scaling |
| `influence_veto` | Veto-power-weighted SC influence | P5 = 10, others = 1 |

**Construction (concise):**
- `influence` = sum over SC members `same_vote_{i,j,y}`
- `influence_gdp` = sum `same_vote_{i,j,y}` * `gdp_normalized_{j,y}`
- `influence_log_gdp` = sum `same_vote_{i,j,y}` * `log_gdp_normalized_{j,y}`
- `influence_veto` = sum `same_vote_{i,j,y}` * `veto_factor_{j}`

**Formula (country i, year y):**  
`influence_{i,y} = sum_{j in SC(y)} same_vote_{i,j,y} * weight_{j,y}`

---

## Set 3. SC members’ external support elsewhere
**Concept:** how much SC attention (via external support to conflicts) is directed outside the country / subregion / region.

| Variable | Meaning | Notes |
| --- | --- | --- |
| `sc_at_war_outside_isocode` | Share of SC support outside the country | `sc_supporter_involved` = # of SC members supporting conflicts in the country-year |
| `sc_at_war_outside_sub_region` | Share of SC support outside the subregion | `involvement_sub_region` = # SC members supporting conflicts in same subregion-year |
| `sc_at_war_outside_region` | Share of SC support outside the region | `involvement_region` = # SC members supporting conflicts in same region-year |

**Construction (concise):**
- `sc_at_war_outside_isocode` = (`total_involvement` - `sc_supporter_involved`) / `total_involvement`
- `sc_at_war_outside_sub_region` = (`total_involvement` - `involvement_sub_region`) / `total_involvement`
- `sc_at_war_outside_region` = (`total_involvement` - `involvement_region`) / `total_involvement`

**Notes:**
- Built from UCDP External Support (state supporters only), filtered to active dyads and SC members by year.  
- Values are in [0, 1]. Missing values default to 1 (full outside involvement), with subregion/region filled by year-level group values when available.

---

## Panel merge conventions
- Set 1 instruments are computed at the country-month level (agreement-month aggregation).  
- Sets 2 and 3 are country-year; merged to all months in that year.  
- Missing values are filled as: Set 1 and Set 2 -> 0; Set 3 -> 1.
