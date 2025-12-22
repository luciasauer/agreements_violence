/*******************************************************************
Project: Peace Agreements Effect on Conflict Intensity
Author: Lucia Sauer
Date: 2025-12-17

Purpose:
Estimate the causal effect of peace agreements on conflict fatalities (log_best)
using Callaway & Sant'Anna's (2021) Difference-in-Differences estimator.
The dataset is a panel at conflict level that spans from 1989-01 to 2024-12, that was simplified using a window generator, where for each window was cutted +-18 months around the treatment, and for control control windows they were randomly assigned.

Treatment definition: 

References:
- Callaway & Sant'Anna (2021): "Difference-in-Differences with Multiple Time Periods"
*******************************************************************/



*******************************************************************
* 1. Import dataset and preprocessing
*******************************************************************
clear all
set more off

local treatment "ceasfire_agreements_mentions"
local matching_method "knn"
local indir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/conflict_level/windows/"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level"

import delimited "`indir'/conflict_windows_`matching_method'_matching_`treatment'.csv", clear

replace is_treated_window = is_treated_window * 18
replace window_t = window_t+18

label var is_treated_window "gvar: treatment month (18=treated, 0=never-treated)"


*******************************************************************
* 2.a Estimate causal effects (CSDID)
*******************************************************************

* Main specification
* Notes:
* - ivar(window_id): window as the treatment unit
* - time(window_t): 0–36 months relative to treatment
* - gvar(treated): 18 for treated, 0 for control
* - dynamic(18): estimate effects up to 18 months post-treatment
* - wboot: wild bootstrap SEs (robust to few clusters)
* - cluster(isocode_main_num): cluster by isocode numeric identifier

* --- Core params
local dyn   18
local grp   18
local seed  1

* --- Main specification
csdid log_best, ivar(window_id_num) time(window_t) gvar(is_treated_window) dynamic(`dyn') method(dripw) cluster(isocode_main_num) wboost rseed(`seed')
estat event, window(-18 18)

* --- Plotting EventStudy
local plot_style ///
    xlabel(-`dyn'(9)`dyn') ///
    yscale(range(-2 2)) ylabel(-2(1)2) ///
    plotregion(fcolor(white)) graphregion(fcolor(white))

local ytitle_main `"ATT on log(fatalities)"'
local xtitle_main `"Months relative to peace agreement"'

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') ///
	xtitle(`"`xtitle_main'"') ///
    `plot_style' ///
    name(g_main, replace)

graph export "`outdir'/eventstudy_`treatment'.pdf", as(pdf) replace name(g_main)

* Display aggregated ATT (overall average treatment effect)
estat simple, wboot


*******************************************************************
* 2.a.i Desaggregating by conflict intensity_level
*******************************************************************

local levels "low_intensity high_intensity"
local gnames "g_low g_high"

local i = 1
foreach lvl of local levels {

    local ttl = cond("`lvl'"=="low_intensity", "Low intensity", "High intensity")
    local gnm : word `i' of `gnames'

    csdid log_best if inlist(intensity_level,"`lvl'","control"), ///
        ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
        dynamic(`dyn') method(dripw) cluster(isocode_main_num) wboost rseed(`seed')

    estat event, window(-`dyn' `dyn')

    * ytitle only on left panel
    local yopt = cond(`i'==1, `"ytitle(`"`ytitle_main'"')"', `"ytitle("")"')

    csdid_plot, group(`grp') ///
        `yopt' ///
        title("`ttl'") ///
		xtitle(`"`xtitle_main'"') ///
        legend(off) ///
        `plot_style' ///
        name(`gnm', replace)

    local ++i
	
	estat simple, wboot

}

graph combine g_low g_high, cols(2) xcommon ycommon ///
    imargin(zero) ///
    graphregion(fcolor(white))
	

graph export "`outdir'/eventstudy_`treatment'_low_high.pdf", as(pdf) replace



*******************************************************************
* 2.a.i Desaggregating by mechanism
*******************************************************************

local mechs "is_has_info_mecha is_has_commit_pol_mecha is_has_commit_econ_mecha is_has_commit_mil_mecha is_has_cost_mecha is_has_balancing_mecha"

local mech_titles `" "Info mechanism" "Political commitment" "Economic commitment" "Military commitment" "Cost mechanism" "Balancing mechanism" "'


local j = 1
foreach m of local mechs {

    local mw "`m'_window"

    * title
    local ttl : word `j' of `mech_titles'

    * graph name
    local gname "g_mech`j'"

    csdid log_best if (`mw' == 1) | (is_treated_window == 0), ///
        ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
        dynamic(`dyn') method(dripw) cluster(isocode_main_num) wboost rseed(`seed')

    estat event, window(-`dyn' `dyn')

	* y-axis label only on left column (panels 1 and 4)
	local yopt = cond(inlist(`j',1,4), `"ytitle(`"`ytitle_main'"')"', `"ytitle("") ylabel(none)"')

	* x-axis label only on bottom row (panels 4,5,6)
	local xopt = cond(`j'<=3, `"xtitle("") xlabel(none)"', `"xtitle("Months relative to peace agreement")"')

    csdid_plot, group(`grp') ///
		`yopt' ///
		`xopt' ///
		title("`ttl'") ///
		legend(off) ///
        `plot_style' ///
        name(`gname', replace)

    local graphlist "`graphlist' `gname'"

    local ++j
	estat simple, wboot
}

graph combine `graphlist', rows(2) cols(3) xcommon ycommon ///
    imargin(zero) ///
    graphregion(fcolor(white)) ///
    name(g_mechs, replace)

graph export "`outdir'/eventstudy_`treatment'_mechanisms.pdf", as(pdf) replace

