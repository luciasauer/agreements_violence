/*******************************************************************
Project: Peace Agreements Effect on Conflict Intensity
Author: Lucia Sauer
Date: 2026-01-07

Purpose:
Estimate the causal effect of peace agreements on conflict fatalities (log_best)
using Callaway & Sant'Anna's (2021) Difference-in-Differences estimator.
The dataset is a panel at conflict level that spans from 1989-01 to 2024-12

Treatment definition: agreement, all agreements 

References:
- Callaway & Sant'Anna (2021): "Difference-in-Differences with Multiple Time Periods"
*******************************************************************/


*******************************************************************
* 1) Import dataset and preprocessing
*******************************************************************

clear all
set more off

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/conflict_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level/first_agreement/"

import delimited using "`indir'/conflict_panel.csv", bindquote(strict) maxquotedrows(unlimited) clear

xtset conflict_id year_mo_numeric
sort conflict_id year_mo_numeric

* Plot style
local plot_style ///
    xlabel(-`dyn'(9)`dyn') ///
    yscale(range(-2 2)) ylabel(-2(1)2) ///
    plotregion(fcolor(white)) graphregion(fcolor(white))

local ytitle_main `"ATT on log(fatalities)"'
local xtitle_main `"Months relative to peace agreement"'


*---Define controls 
local conflict_age_dummies conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m

preserve
keep if (treated_agreement == 0) | (high_intensity == 0)	
csdid2 log_best `conflict_age_dummies', ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph export "`outdir'/event_baseline_LOW.png", as(png) replace
csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "baseline_LOW"
restore

preserve
keep if (treated_agreement == 0) | (high_intensity == 1)	
csdid2 log_best `conflict_age_dummies', ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph export "`outdir'/event_baseline_HIGH.png", as(png) replace
csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "baseline_HIGH"
restore



*******************************************************************
* 4) Close collector + export cevent results
*******************************************************************
postclose `ph'

use `results_cevent', clear
order spec att se lb ub pval
sort spec

save "`outdir'/cevent_att_1_18_wboot.dta", replace
export delimited using "`outdir'/cevent_att_1_18_wboot.csv", replace


