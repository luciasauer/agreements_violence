*******************************************************************
* 0. Setup
*******************************************************************
clear all
set more off

local treatment "ceasfire_agreements_mentions"
local matching_method "random"
*local matching_variable "gdp_pc_current_usd_lag1"

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/country_level/windows"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/country_level/`matching_method'_matching"

if strlen("`matching_variable'") == 0 {
    import delimited "`indir'/country_windows_`matching_method'_matching_`treatment'.csv", clear
}
else {
    import delimited "`indir'/country_windows_`matching_method'_`matching_variable'_`treatment'.csv", clear
}

* Ensure output folder exists
capture mkdir "`outdir'"
capture mkdir "`outdir'/`treatment'"

* gvar = 18 treated, 0 control
replace is_treated_window = is_treated_window * 18
replace window_t = window_t + 18
label var is_treated_window "gvar: treatment month (18=treated, 0=never-treated)"

xtset window_id_num window_t
sort window_id_num window_t

* Core params
local dyn   18
local grp   18
local seed  1

* Plot style
local plot_style ///
    xlabel(-`dyn'(9)`dyn') ///
    yscale(range(-2 2)) ylabel(-2(1)2) ///
    plotregion(fcolor(white)) graphregion(fcolor(white))

local ytitle_main `"ATT on log(fatalities)"'
local xtitle_main `"Months relative to peace agreement"'


*******************************************************************
* 0.1 Collector: store estat simple (wboot) results and export to Excel
*******************************************************************
tempname fh
tempfile results_es

* Columns: spec name + ATT + SE + CI + p-value (from estat simple, wboot)
postfile `fh' ///
    str60 spec ///
    double att se lb ub pval ///
    using `results_es', replace

capture program drop _collect_simple
program define _collect_simple
    args ph specname

    // Debe ejecutarse INMEDIATAMENTE tras: estat simple, wboot
    matrix T = r(table)

    // extrae números a escalares/locales
    scalar att  = T[1,1]
    scalar se   = T[2,1]
    scalar pval = T[4,1]
    scalar lb   = T[5,1]
    scalar ub   = T[6,1]

    post `ph' ("`specname'") (att) (se) (lb) (ub) (pval)
end

*******************************************************************
* 1. Diagnostics: Within-window volatility
*******************************************************************

* sd(log_best) within each window
bys window_id_num: egen sd_y = sd(log_best)

hist sd_y, fraction ///
    xtitle("SD of Log Fatalities within-window ") ///
    ytitle("Density") ///
    name(h_sd_y, replace)

graph export "`outdir'/`treatment'/diagnostic_hist_within_window_sd_y.png", ///
    as(png) replace name(h_sd_y)

*******************************************************************
* 2. Diagnostics: SD by event time
*******************************************************************

preserve
collapse (sd) sd_t=log_best (mean) mean_t=log_best, by(window_t)

twoway line sd_t window_t, ///
    xtitle("window_t") ytitle("SD of Log Fatalities") ///
    name(g_sd_by_t, replace)

graph export "`outdir'/`treatment'/diagnostic_sd_by_event_time.png", ///
    as(png) replace name(g_sd_by_t)
restore


*******************************************************************
* 3. Diagnostics: Pre-post change per window (treated vs control)
*******************************************************************

* Define base and post (ejemplo: +6 meses post = window_t=24)
bys window_id_num: egen y_base  = max(cond(window_t==17, log_best, .))
bys window_id_num: egen y_post6 = max(cond(window_t==24, log_best, .))
gen dy6 = y_post6 - y_base

preserve
keep if window_t==17  // 1 obs por ventana

* Densidades superpuestas
twoway ///
(kdensity dy6 if is_treated_window==18) ///
(kdensity dy6 if is_treated_window==0), ///
legend(order(1 "Treated windows" 2 "Control windows")) ///
xtitle("dy6 = log_best(t=24) - log_best(base=17)") ///
ytitle("Density") ///
name(g_dy6_kdens, replace)

graph export "`outdir'/`treatment'/diagnostic_dy6_density_treated_control.png", ///
    as(png) replace name(g_dy6_kdens)

* Boxplot comparativo
graph box dy6, over(is_treated_window) ///
    ytitle("dy6") ///
    name(g_dy6_box, replace)

graph export "`outdir'/`treatment'/diagnostic_dy6_box_treated_control.png", ///
    as(png) replace name(g_dy6_box)

restore


*******************************************************************
* 4. Controls construction
*******************************************************************

* --- GDP: Mean of 6 lags (MA6)
egen log_gdp_pc_ma6 = rowmean(log_gdp_pc_current_usd_lag1-log_gdp_pc_current_usd_lag6)

* --- GDP base (pre-treatment last month)
bys window_id_num: egen gdp_base = max(cond(window_t==17, log_gdp_pc_current_usd, .))

* --- Outcome severity controls (pre-treatment)
* average last 6 months before treatment: 12..17
bys window_id_num: egen y_pre6 = mean(cond(inrange(window_t,12,17), log_best, .))

* average "further away" pre: 6..12 (robustness vs anticipation)
bys window_id_num: egen y_pre_far = mean(cond(inrange(window_t,6,12), log_best, .))


* 1 obs por ventana
preserve
keep if window_t==17

* sd_y ya creado: SD(log_best) dentro de ventana
reg sd_y gdp_base if !missing(sd_y, gdp_base), vce(robust)
di "R2 = " e(r2)

twoway (scatter sd_y gdp_base) (lfit sd_y gdp_base), ///
    xtitle("GDP per capita (baseline, log)") ///
    ytitle("Within-window SD of log fatalities") ///
    name(g_sdy_gdp, replace)

graph export "`outdir'/`treatment'/diag_sdy_on_gdp_base.png", as(png) replace name(g_sdy_gdp)
restore


* Check windows that will be used when controlling by lags of log_gdp_pc
gen sample_gdp6 = !missing(log_best, ///
    log_gdp_pc_current_usd_lag1, log_gdp_pc_current_usd_lag2, ///
    log_gdp_pc_current_usd_lag3, log_gdp_pc_current_usd_lag4, ///
    log_gdp_pc_current_usd_lag5, log_gdp_pc_current_usd_lag6)
bys window_id_num: egen window_ok_gdp6 = min(sample_gdp6)
tab is_treated_window if window_ok_gdp6==1


*******************************************************************
* 5. Estimation: Baseline (no controls)
*******************************************************************

csdid log_best, ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
    dynamic(`dyn') method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_base, replace)

graph export "`outdir'/`treatment'/eventstudy_baseline.png", ///
    as(png) replace name(g_base)

*estat simple, wboot
estat cevent, window(1 18) wboot

_collect_simple `fh' "baseline_no_controls"


*******************************************************************
* 6. Estimation: Baseline by low vs high pre-treatment violence
*******************************************************************

local levels "low_intensity high_intensity"
local gnames "g_low g_high"

local i = 1
foreach lvl of local levels {

    local ttl = cond("`lvl'"=="low_intensity", "Low intensity", "High intensity")
    local gnm : word `i' of `gnames'

    csdid log_best if inlist(intensity_level,"`lvl'","control"), ///
        ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
        dynamic(`dyn') method(dripw) cluster(isocode_num) wboost rseed(`seed')

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
	estat cevent, window(1 18)
    _collect_simple `fh' "`lvl'_intensity"

}

graph combine g_low g_high, cols(2) xcommon ycommon ///
    imargin(zero) ///
    graphregion(fcolor(white))	

graph export "`outdir'/`treatment'/eventstudy_low_high.png", as(png) replace


*******************************************************************
* 7. Estimation: Baseline by mechanism
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
        dynamic(`dyn') method(dripw) cluster(isocode_num) wboost rseed(`seed')

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
	estat cevent, window(1 18)
    _collect_simple `fh' "`m'"
}

graph combine `graphlist', rows(2) cols(3) xcommon ycommon ///
    imargin(zero) ///
    graphregion(fcolor(white)) ///
    name(g_mechs, replace)

graph export "`outdir'/`treatment'/eventstudy_mechanisms.pdf", as(pdf) replace

*******************************************************************
* 8. Estimation: GDP control (MA6 of lags)
*******************************************************************

csdid log_best log_gdp_pc_ma6, ///
    ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
    dynamic(`dyn') method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_gdp_ma6, replace)

graph export "`outdir'/`treatment'/eventstudy_gdp_ma6.png", ///
    as(png) replace name(g_gdp_ma6)


* ---- Store results (GDP MA6)
*estat simple, wboot
estat cevent, window(1 18) wboot
_collect_simple `fh' "gdp_control_ma6"

*******************************************************************
* 9. Estimation: GDP control (base-period)
*******************************************************************

csdid log_best gdp_base, ///
    ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
    dynamic(`dyn') method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_gdp_base, replace)

graph export "`outdir'/`treatment'/eventstudy_gdp_base.png", ///
    as(png) replace name(g_gdp_base)

*estat simple, wboot

* ---- Store results (GDP base)
*estat simple, wboot
estat cevent, window(1 18) wboot
_collect_simple `fh' "gdp_control_base_period"

*******************************************************************
* 10. Estimation: Control for pre-treatment severity (y_base)
*******************************************************************

csdid log_best y_base, ///
    ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
    dynamic(`dyn') method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_y_base, replace)

graph export "`outdir'/`treatment'/eventstudy_control_y_base.png", ///
    as(png) replace name(g_y_base)


* ---- Store results (control y_base)
*estat simple, wboot
estat cevent, window(1 18) wboot
_collect_simple `fh' "control_pre_severity_y_base"


*******************************************************************
* 11. Estimation: Control for pre-treatment severity (y_pre6)
*******************************************************************

csdid log_best y_pre6, ///
    ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
    dynamic(`dyn') method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_y_pre6, replace)

graph export "`outdir'/`treatment'/eventstudy_control_y_pre6.png", ///
    as(png) replace name(g_y_pre6)


* ---- Store results (control y_pre6)
*estat simple, wboot
estat cevent, window(1 18) wboot
_collect_simple `fh' "control_pre_severity_y_pre6"


*******************************************************************
* 12. Aggregate windows into quarters
*******************************************************************
	
* quarter within the window
gen q_t = ceil(window_t/3)

* gvar in quarter scale
gen is_treated_window_q = cond(is_treated_window==18, ceil(18/3), 0)
label var is_treated_window_q "gvar quarterly (6=treated quarter, 0=never-treated)"

bys window_id_num q_t: egen fatal_q = total(best)
gen log_best_q = log(fatal_q + 1)

preserve
keep window_id_num isocode_num q_t is_treated_window_q log_best_q
bys window_id_num q_t: keep if _n==1
xtset window_id_num q_t

csdid log_best_q, ///
  ivar(window_id_num) time(q_t) gvar(is_treated_window_q) ///
  dynamic(6) method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-6 6)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    yscale(range(-2 2)) ylabel(-2(1)2) plotregion(fcolor(white)) graphregion(fcolor(white)) ///
    name(g_base_q, replace)
	
*estat simple, wboot
estat cevent, window(1 6) wboot
_collect_simple `fh' "quarterly_outcome_log_best_q"

graph export "`outdir'/`treatment'/eventstudy_baseline_quarterly.png", ///
    as(png) replace name(g_base_q)

restore


*******************************************************************
* 13. Transform outcome into rolling means to smooth VAR(y)
*******************************************************************
	
xtset window_id_num window_t

gen fatal_ma3 = (best + L1.best + L2.best)/3
gen log_best_ma3 = log(fatal_ma3 + 1)

csdid log_best_ma3, ///
  ivar(window_id_num) time(window_t) gvar(is_treated_window) ///
  dynamic(18) method(dripw) cluster(isocode_num) wboot rseed(`seed')

estat event, window(-18 18)

csdid_plot, group(`grp') ///
    ytitle(`"`ytitle_main'"') xtitle(`"`xtitle_main'"') ///
    `plot_style' name(g_base_MA, replace)


*estat simple, wboot
estat cevent, window(1 18) wboot
_collect_simple `fh' "rolling_mean_outcome_log_best_ma3"

graph export "`outdir'/`treatment'/eventstudy_baseline_MA3.png", ///
    as(png) replace name(g_base_MA)


*******************************************************************
* 14. Export appended regression results to Excel
*******************************************************************
postclose `fh'
use `results_es', clear
list, noobs abbreviate(20)
summ att se lb ub pval


export excel using "`outdir'/`treatment'/csdid_estat_simple_results.xlsx", ///
    firstrow(variables) replace

putexcel set "`outdir'/`treatment'/csdid_estat_simple_results.xlsx", modify
local last = _N + 1   // +1 por el header en la fila 1

