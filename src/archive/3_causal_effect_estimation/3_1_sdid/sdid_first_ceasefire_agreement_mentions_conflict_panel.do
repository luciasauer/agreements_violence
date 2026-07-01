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

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level/first_agreement/"

import delimited using "`indir'/conflict_panel.csv", bindquote(strict) maxquotedrows(unlimited)  clear


xtset conflict_id year_mo_numeric

bysort conflict_id (year_mo_numeric): egen first_agreement = min(cond(agreement==1, year_mo_numeric, .))

gen ever = !missing(first_agreement)

*define treatment as starting month after
gen D = (year_mo_numeric > first_agreement) & ever

*fitler by 1990-01
drop if first_agreement<13


*******************************************************************
* SDID ceasefire_agreement
*******************************************************************

*keep if year_mo_numeric <= first_agreement + 18 | ever==0

sdid log_best conflict_id year_mo_numeric D, vce(placebo)  


sdid log_best conflict_id mdate D, ///
    vce(placebo) reps(50) ///
    graph g1on ///
    g1_opt( ///
        title("Unit weights") ///
        xtitle("Control conflicts") ///
        ytitle("Weight") ///
        msize(small) ///
    ) ///
    g2_opt( ///
        title("Treated vs synthetic control") ///
        xtitle("Month") ///
        ytitle("log(best+1)") ///
        legend(pos(6) cols(1)) ///
        scheme(s1color) ///
    ) ///
    xline_opts(lcolor(red) lpattern(dash) lwidth(medthick)) ///
    yline_opts(lcolor(gs8) lpattern(shortdash))
	
sdid_event log_best conflict_id year_mo_numeric D, effects(6) placebo(6) vce(placebo) brep(20)


clear all
set more off

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level/first_agreement/"

import delimited using "`indir'/conflict_data_filtered.csv", bindquote(strict) maxquotedrows(unlimited)  clear

sdid_event log_best conflict_id year_mo_numeric d_first_agreement_active, effects(6) placebo(6) vce(placebo) brep(20)




* ==============================================================================
* PANEL SEMESTRAL
* ==============================================================================

clear all
set more off

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/event_study/conflict_level/first_agreement/"

import delimited using "`indir'/conflict_data_filtered_semester.csv", bindquote(strict) maxquotedrows(unlimited)  clear



* Ordenar datos
sort conflict_id year_semester

xtset conflict_id year_semester

sdid log_best conflict_id year_semester d_first_agreement_active, vce(placebo)  


sdid log_best conflict_id year_semester d_first_agreement_active, ///
    vce(placebo) reps(50) ///
    graph g1on ///
    g1_opt( ///
        title("Unit weights") ///
        xtitle("Control conflicts") ///
        ytitle("Weight") ///
        msize(small) ///
    ) ///
    g2_opt( ///
        title("Treated vs synthetic control") ///
        xtitle("Month") ///
        ytitle("log(best+1)") ///
        legend(pos(6) cols(1)) ///
        scheme(s1color) ///
    ) ///
    xline_opts(lcolor(black) lpattern(dash) lwidth(medthick)) ///
    yline_opts(lcolor(gs8) lpattern(shortdash))


    
* Correr sdid_event a nivel semestral
sdid_event log_best conflict_id year_semester d_first_agreement_active, ///
    effects(3) placebo(3) vce(placebo) brep(20)
	

* Correr sdid_event a nivel semestral
sdid_event log_best conflict_id year_semester d_first_agreement_active, ///
    effects(6) placebo(6) vce(placebo) brep(20)
