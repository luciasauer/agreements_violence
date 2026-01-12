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

*Installation of csdid2 for long panels
cap which csdid2
if _rc{
	net install csdid2, from("https://friosavila.github.io/stpackages")
}


*******************************************************************
* 1) Import dataset and preprocessing
*******************************************************************

clear all
set more off

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level/first_agreement/"

import delimited using "`indir'/conflict_panel.csv", bindquote(strict) maxquotedrows(unlimited)  clear

xtset conflict_id year_mo_numeric
sort conflict_id year_mo_numeric

* Plot style
local plot_style ///
    xlabel(-`dyn'(9)`dyn') ///
    yscale(range(-2 2)) ylabel(-2(1)2) ///
    plotregion(fcolor(white)) graphregion(fcolor(white))

local ytitle_main `"ATT on log(fatalities)"'
local xtitle_main `"Months relative to peace agreement"'

*******************************************************************
* 2) Collector for csdid2_estat cevent, revent(1/18) wboot
*******************************************************************
tempname ph
tempfile results_cevent

postfile `ph' ///
    str60 spec ///
    double att se lb ub pval ///
    using `results_cevent', replace

capture program drop _collect_cevent_wboot
program define _collect_cevent_wboot
    // run immediately after: csdid2_estat cevent, revent(1/18) wboot
    args ph specname

    matrix T = r(table)

    scalar att  = T[1,1]
    scalar se   = T[2,1]
    scalar pval = T[4,1]
    scalar lb   = T[5,1]
    scalar ub   = T[6,1]

    post `ph' ("`specname'") (att) (se) (lb) (ub) (pval)
end



*******************************************************************
* 3) Estimate causal effects (CSDID) Agreements
*******************************************************************

{
* Main specification
* Notes:
* - ivar(window_id): window as the treatment unit
* - time(window_t): 0–36 months relative to treatment
* - gvar(treated): 18 for treated, 0 for control
* - dynamic(18): estimate effects up to 18 months post-treatment
* - wboot: wild bootstrap SEs (robust to few clusters)
* - cluster(window_id): cluster by window id (episodes)
}

*------------------------------*
* (A) Baseline
*------------------------------*
{
csdid2 log_best, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)

* Event study plot (wboot) + export
estat event, window(-18 18) wboot plot
graph rename Graph g_baseline, replace
graph export "`outdir'/event_baseline.png", as(png) replace name(g_baseline)

* Cumulative event 1..18 excluding 0 + wboot + collect
csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "baseline"
}


*------------------------------*
* (B) Age dummies
*------------------------------*

*---Define controls 
local conflict_age_dummies conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m

* Controlling for the conflict_age as dummies 
{
csdid2 log_best `conflict_age_dummies', ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph rename Graph g_age, replace
graph export "`outdir'/event_age.png", as(png) replace name(g_age)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies"
}


*------------------------------*
* (C) Age dummies + region FE
*------------------------------*
* Controlling for the conflict_age as dummies + region 
{
csdid2 log_best `conflict_age_dummies' i.region_num, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph rename Graph g_age, replace
graph export "`outdir'/event_age_region.png", as(png) replace name(g_age)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies_region"
}


*------------------------------*
* (D) Age dummies + duration
*------------------------------*

* Controlling for the conflict_age as dummies + duration_months as end_date - start_date
{
csdid2 log_best `conflict_age_dummies' duration_months, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph rename Graph g_age, replace
graph export "`outdir'/event_age_duration.png", as(png) replace name(g_age)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies_duration"
}


*------------------------------*
* (E) Age dummies + log GDP pc
*------------------------------*
{
csdid2 log_best `conflict_age_dummies' log_gdp_pc_current_usd, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)

estat event, window(-18 18) wboot plot
graph rename Graph g_age_gdp, replace
graph export "`outdir'/event_age_gdp.png", as(png) replace name(g_age_gdp)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies_gdp"
}


*------------------------------*
* (F) Age dummies + GDP pc + month-of-year FE
*     (captures seasonality in violence/reporting)
*------------------------------*
{
csdid2 log_best `conflict_age_dummies' log_gdp_pc_current_usd i.current_month, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)

estat event, window(-18 18) wboot plot
graph rename Graph g_age_gdp_m, replace
graph export "`outdir'/event_age_gdp_monthFE.png", as(png) replace name(g_age_gdp_m)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies_gdp_monthFE"
}


*------------------------------*
* (G) Age dummies + GDP pc + month FE + country FE
*     (absorbs time-invariant country differences)
*------------------------------*
{
*csdid2 log_best `conflict_age_dummies' log_gdp_pc_current_usd i.current_month i.isocode_num, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)

*estat event, window(-18 18) wboot plot
*graph rename Graph g_age_gdp_m_cty, replace
*graph export "`outdir'/event_age_gdp_monthFE_countryFE.png", as(png) replace name(g_age_gdp_m_cty)

*csdid2_estat cevent, revent(1/18) wboot
*_collect_cevent_wboot `ph' "age_dummies_gdp_monthFE_countryFE"
}


*------------------------------*
* (H) Age dummies + GDP pc + region×year FE (+ month FE)
*     (captures regional shocks that vary by year)
*------------------------------*
{
csdid2 log_best `conflict_age_dummies' log_gdp_pc_current_usd i.current_month i.region_num#i.year, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)

estat event, window(-18 18) wboot plot
graph rename Graph g_age_gdp_m_regyr, replace
graph export "`outdir'/event_age_gdp_monthFE_regionXyear.png", as(png) replace name(g_age_gdp_m_regyr)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_dummies_gdp_monthFE_regionXyear"
}


*------------------------------*
* (I) Pre violence controls
*------------------------------*
{
* Identify treated conflicts (first_agreement_date > 0 and not missing)
gen byte ever_treated = (first_agreement_date < . & first_agreement_date > 0)

* Relative time to first agreement (only for treated)
gen int rel_m = year_mo_numeric - first_agreement_date if ever_treated

* Helpers for pre-window (-12..-1)
gen byte pre12 = ever_treated & inrange(rel_m, -12, -1)

* For never-treated conflicts (controls), all months are "pre" by definition
gen byte never_treated = (ever_treated==0)

* --- mean/sd in pre window for treated; for controls use full sample mean/sd
by conflict_id: egen double pre_mean12_t = mean(best) if pre12
by conflict_id: egen double pre_sd12_t   = sd(best)   if pre12
by conflict_id: egen double pre_zero12_t = mean(best==0) if pre12

by conflict_id: egen double pre_mean12_c = mean(best) if never_treated
by conflict_id: egen double pre_sd12_c   = sd(best)   if never_treated
by conflict_id: egen double pre_zero12_c = mean(best==0) if never_treated

gen double pre_mean12_best = pre_mean12_t
replace pre_mean12_best = pre_mean12_c if missing(pre_mean12_best) & never_treated

gen double pre_sd12_best = pre_sd12_t
replace pre_sd12_best = pre_sd12_c if missing(pre_sd12_best) & never_treated

gen double pre_share_zero12 = pre_zero12_t
replace pre_share_zero12 = pre_zero12_c if missing(pre_share_zero12) & never_treated

* log versions
gen double log_pre_mean12 = log(pre_mean12_best + 1)

* Cap extreme pre controls to reduce leverage (winsorize-like)
egen double p99_pre = pctile(pre_mean12_best), p(99)
replace pre_mean12_best = p99_pre if pre_mean12_best > p99_pre & p99_pre < .
replace log_pre_mean12  = log(pre_mean12_best + 1)
drop p99_pre

local pre_violence "log_pre_mean12 pre_sd12_best pre_share_zero12"

*---------------------------------------------------------------*
* Spec: age dummies + pre-violence
*---------------------------------------------------------------*
{
csdid2 log_best `conflict_age_dummies' `pre_violence', ///
    ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) ///
    notyet method(dripw) cluster(isocode_num)

estat event, window(-18 18) wboot plot
graph rename Graph g_age_pre_violence, replace
graph export "`outdir'/event_age_pre_violence.png", as(png) replace name(g_age_pre_violence)

csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "age_pre_violence"
}
}


*------------------------------*
* (J) Low/High Violence Intensity Pretreatment
*------------------------------*
{
*------Low Violence Intensity	
preserve
keep if (treated_agreement == 0) | (high_intensity == 0)	
csdid2 log_best `conflict_age_dummies', ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph export "`outdir'/event_baseline_LOW.png", as(png) replace
csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "baseline_LOW"
restore

*------High Violence Intensity	
preserve
keep if (treated_agreement == 0) | (high_intensity == 1)	
csdid2 log_best `conflict_age_dummies', ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_num)
estat event, window(-18 18) wboot plot
graph export "`outdir'/event_baseline_HIGH.png", as(png) replace
csdid2_estat cevent, revent(1/18) wboot
_collect_cevent_wboot `ph' "baseline_HIGH"
restore
}


*------------------------------*
* (K) QUARTERLY PANEL 
*------------------------------*
{
preserve

* Convert month index (1989-01 = 1) -> Stata monthly %tm
local base_tm = tm(1989m1)
cap drop ym_tm start_tm agree_tm
gen int ym_tm    = `base_tm' + (year_mo_numeric - 1)
gen int start_tm = `base_tm' + (start_date_numeric - 1)
gen int agree_tm = `base_tm' + (first_agreement_date - 1) if first_agreement_date<.
format ym_tm start_tm agree_tm %tm

* Build quarterly time
cap drop qtr first_agreement_q
gen int qtr = qofd(dofm(ym_tm))
format qtr %tq

gen int first_agreement_q = qofd(dofm(agree_tm)) if agree_tm<.
format first_agreement_q %tq
* Collapse to conflict_id x isocode x quarter
collapse ///
    (sum) best ///
    (mean) log_gdp_pc_current_usd ///
    (first) region_num ///
    (first) first_agreement_q ///
    (first) start_tm ///
    , by(conflict_id isocode_num qtr)

* Outcome quarterly
gen double log_best_q = log(best + 1)

* Panel
xtset conflict_id qtr
sort conflict_id qtr

* Baseline quarterly
{
csdid2 log_best_q, ivar(conflict_id) tvar(qtr) gvar(first_agreement_q) notyet method(dripw) cluster(isocode_num)

estat event, window(-6 6) wboot plot
graph rename Graph g_q_baseline, replace
graph export "`outdir'/event_quarterly_baseline.png", as(png) replace name(g_q_baseline)

csdid2_estat cevent, revent(1/6) wboot
_collect_cevent_wboot `ph' "q_baseline_1to6"
}

* Conflict age in quarters (now start_tm is %tm and survives collapse)
gen int start_q = qofd(dofm(start_tm))
format start_q %tq
gen int conflict_age_q = qtr - start_q

*---------------------------------------------------------------*
* Conflict age dummies (bins) in quarters
*---------------------------------------------------------------*
cap drop conflict_age_bin
gen byte conflict_age_bin = .

* Ejemplo de bins: 0-1q (0-6m), 2-3q (6-12m), 4-5q (12-18m),
* 6-7q (18-24m), 8-9q (24-30m), 10+ (30m+)
replace conflict_age_bin = 1 if inrange(conflict_age_q, 0, 1)
replace conflict_age_bin = 2 if inrange(conflict_age_q, 2, 3)
replace conflict_age_bin = 3 if inrange(conflict_age_q, 4, 5)
replace conflict_age_bin = 4 if inrange(conflict_age_q, 6, 7)
replace conflict_age_bin = 5 if inrange(conflict_age_q, 8, 9)
replace conflict_age_bin = 6 if conflict_age_q >= 10 & conflict_age_q < .

label define agebin_q ///
    1 "0-6m" ///
    2 "6-12m" ///
    3 "12-18m" ///
    4 "18-24m" ///
    5 "24-30m" ///
    6 "30m+"
label values conflict_age_bin agebin_q

* check
tab conflict_age_bin, missing


* Adding control: conflict_age (quarterly)
{
csdid2 log_best_q i.conflict_age_bin, ivar(conflict_id) tvar(qtr) gvar(first_agreement_q) notyet method(dripw) cluster(isocode_num)
	
estat event, window(-6 6) wboot plot
graph rename Graph g_q_age, replace
graph export "`outdir'/event_quarterly_age.png", as(png) replace name(g_q_age)

csdid2_estat cevent, revent(1/6) wboot
_collect_cevent_wboot `ph' "q_baseline_1to6_age"
}

}



*******************************************************************
* 4) Close collector + export cevent results
*******************************************************************
postclose `ph'

use `results_cevent', clear
order spec att se lb ub pval
sort spec

export delimited using "`outdir'/cevent_att_1_18_wboot.csv", replace


