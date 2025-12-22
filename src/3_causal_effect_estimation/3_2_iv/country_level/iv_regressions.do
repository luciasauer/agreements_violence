/* -------------------------------------------------------------- */
/* CAUSAL EFFECT OF CONFLICT POLICY                               */
/* XTREG AND IV REGRESSIONS 					                  */
/* Author: Lucia Sauer         			                          */
/* Last update:                                      */
/* -------------------------------------------------------------- */


clear all
local treatment "ceasfire_agreements_mentions"
local indir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/country_level/"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/iv_regressions"

import delimited "`indir'/country_panel.csv", clear 



// Gen fatalities in previous month (we filter for this in two of the models later)
rangestat (mean) best_prevm=best, interval(year_mo -1 -1) by(isocode)

*** Generate variables ***
**************************
egen countryid = group(isocode)                 // Create a variable 'countryid' representing groups of 'isocode'
gen ym = ym(year, month)                        // Create a variable 'ym' representing year-month combination from 'year' and 'month'
tab ym, gen(ym_)                                // Generate a table of the 'ym' variable and generate new variables 'ym_' based on the table
xtset countryid ym                                // XTSET command is best for panel data with more than one individual, (country), since it also sets the ID
tab countryid, gen(countryid_)                  // Generate a table of the 'countryid' variable and generate new variables 'countryid_' based on the table



* Several options for variable capturing "influential friends": (take average of last 12 months)
*          influence_score == how close I am to those in security council (all not just premanent members)
*          influence_gdp == how similar voting behavior to those in security council (weighted by GDP) (all not just permanent members)
*          influence_veto == same as influence score, but weighting permenant members by 10 

* Other IVs
*    'n_agreement_outside_isocode':'number of agreements outside the country', 
*    'n_agreement_outside_region':'number of agreements outside the region of the country',
*    'n_agreement_outside_sub_region':'number of agreements outside the subregion of the country',
*    'sc_at_war_year':'total number security council members at war that year',
*    'sc_at_war_outside_isocode':'number of security council members at war outside of the country',
*    'sc_at_war_outside_sub_region':'number of security council members at war outside the subregion of the country',
*    'sc_at_war_outside_region':'number of security council members at war outside the region of the country',


// create 18 lags of log best
forvalues i = 1/18 { 
    gen lag_log_best`i' = L`i'.log_best
}

// create 18 FUTURES of log best
forvalues i = 1/18 { 
    gen fut_log_best`i' = F`i'.log_best
    gen fut_best`i'=F`i'.best
}

// Create average of 3 months future fatalities
egen fut_log_best3_m =rowmean(fut_log_best1 fut_log_best2 fut_log_best3)

forvalues i = 1/12 { 
gen lag_log_best`i'_friends = L`i'.log_best*influence_veto_past_12
}

sort isocode year_mo


encode region, gen(region_n)

bysort ym: egen otheragreement_ym=sum(agreement)
replace otheragreement_ym=otheragreement_ym-agreement


global outcome_fe log_best // Define the single outcome variable
global controls_fe lag_log_best1- lag_log_best6 // Define the control variables
global outcome_future fut_log_best3_m


*** Regressions, IV ***
**********************************

/// 1st TYPE OF INTSTRUMENTS: INSTRUMENTS RELATED TO INFLUENCE SCORES IN UN VOTING

***** Examining first stage *****
**Weighted influence score Ivs***
*********************************

//agreement on influence_veto_past_12 (Veto and friendship UN)
xtreg agreement_count influence_veto_past_12 $controls_fe if year >= 1990 & year <= 2022 & 	influence > 0, fe r cluster(countryid)
test influence_veto_past_12
outreg2 using ""`indir'/first_stage.xls", replace excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//agreement on influence_gdp_past_12 (GDP and friendship UN)
xtreg agreement_count influence_gdp_past_12 $controls_fe if year >= 1990 & year <= 2022 & influence > 0, fe r cluster(countryid)
test influence_gdp_past_12
outreg2 using ""`indir'/first_stage.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))


*** IV regressions ***
**Agreements in region/subregion Ivs
// First Model
// instrument using influence_veto_past_12 - voting similarity to those in the security council, weighting by veto power.
xtivreg $outcome_fe (agreement_count = influence_veto_past_12 *_friends) $controls_fe  if year >= 1990 & year <= 2022 & influence > 0, vce(cluster countryid)
    outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_`k'.xls", replace excel bdec(3) sdec(3) slow(100) label

// Second Model	
// Variation of average future 3 months outcome
xtivreg $outcome_future (agreement_count = influence_veto_past_12 *_friends) $controls_fe  if year >= 1990 & year <= 2022 & influence > 0, vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

// Fifht Model	
xtivreg $outcome_fe (agreement_count = influence_gdp_past_12 *_friends) $controls_fe  if year >= 1990 & year <= 2022 & influence > 0, vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

// Sixth Model
// Variation of fatalities in last month larger than 0
xtivreg $outcome_fe (agreement_count = influence_veto_past_12 *_friends) $controls_fe  if year >= 1990 & year <= 2022 & influence > 0 & (best_prevm>0 & best_prevm!=.), vce(cluster countryid)		
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

// Seventh Model
// Variation of average future 3 months outcome
xtivreg $outcome_future (agreement_count = influence_veto_past_12 *_friends) $controls_fe  if year >= 1990 & year <= 2022 & influence > 0 & (best_prevm>0 & best_prevm!=.), vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

    
    
/// 2n TYPE OF INTSTRUMENTS: INSTRUMENTS RELATED TO PAST PEACE AGREEMENTS IN REGION, EXCLUDING OWN

*** Examining first stage, for variation of count of agreements only when conflict exists ***	
//First Model
// agreement on weighted average of peace agreements in the region (excluding country c) in the last X years (X=1,5) with distance weight
xtreg agreement_count agree_region_out_p${chosen_range}_wdist $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)	
test agree_region_out_p${chosen_range}_wdist 
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", replace excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))
        
//Second Model
xtreg agreement_count agree_subreg_out_p${chosen_range}_wdist $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_subreg_out_p${chosen_range}_wdist 
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))
    
//Third Model
// agreement on weighted average of peace agreements in the region (excluding country c) in the last X years (X=1,5) with trade weight
xtreg agreement_count agree_region_out_p${chosen_range}_wtrade $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_region_out_p${chosen_range}_wtrade 
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Fourth Model
xtreg agreement_count agree_subreg_out_p${chosen_range}_wtrade $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_subreg_out_p${chosen_range}_wtrade
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Fifth Model
// agreement on Total number of peace agreements in the last X years (X=1, 5) in the region of country c (excluding c) times number of fatalities in country c last year
xtreg agreement_count agree_region_out_p${chosen_range}_wfatal $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_region_out_p${chosen_range}_wfatal
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Sixth Model
xtreg agreement_count agree_subreg_out_p${chosen_range}_wfatal $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_subreg_out_p${chosen_range}_wfatal
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Seventh Model
// Variation with dummy
xtreg agreement agree_region_out_p${chosen_range}_wfatal_d $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_region_out_p${chosen_range}_wfatal_d
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Eight Model
xtreg agreement agree_subreg_out_p${chosen_range}_wfatal_d $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test agree_subreg_out_p${chosen_range}_wfatal_d
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))
    
//Nineth Model		
// agreement on SHARE of number of peace agreements in the last X years (X=1, 5) in the region of country c (excluding c) times number of fatalities in country c last year
xtreg agreement_count share_agree_region_p${chosen_range}_wfatal $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test share_agree_region_p${chosen_range}_wfatal
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))

//Tenth Model		
xtreg agreement_count share_agree_subreg_p${chosen_range}_wfatal $controls_fe  if year >= 1990 & year <= 2022, fe r cluster(countryid)
test share_agree_subreg_p${chosen_range}_wfatal
outreg2 using "$HPresults/tables/regressions/regressions_iv/first_stage_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label addstat("F-stat", r(F))
    

*** IV regressions ***
xtivreg $outcome_fe (agreement_count = agree_region_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", replace excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = agree_subreg_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
// Variation using outcome that is average of 3 future months of fatalities		
xtivreg $outcome_future (agreement_count = agree_subreg_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label


xtivreg $outcome_fe (agreement_count = agree_region_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = agree_subreg_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
// Variation using outcome that is average of 3 future months of fatalities
        
xtivreg $outcome_future (agreement_count = agree_subreg_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

    
xtivreg $outcome_fe (agreement_count = agree_region_out_p${chosen_range}_wfatal) $controls_fe  if year >= 1990 & year <= 2022, fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = agree_subreg_out_p${chosen_range}_wfatal) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
xtivreg $outcome_fe (agreement = agree_region_out_p${chosen_range}_wfatal_d) $controls_fe  if year >= 1990 & year <= 2022, fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement = agree_subreg_out_p${chosen_range}_wfatal_d) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = share_agree_region_p${chosen_range}_wfatal) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
xtivreg $outcome_fe (agreement_count = share_agree_subreg_p${chosen_range}_wfatal) $controls_fe if year >= 1990 & year <= 2022, fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

            
            
// Variation with only months with fatalities
xtivreg $outcome_fe (agreement_count = agree_region_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = agree_subreg_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)	
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
// Variation using outcome that is average of 3 future months of fatalities
xtivreg $outcome_future (agreement_count = agree_subreg_out_p${chosen_range}_wdist) $controls_fe  if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label


xtivreg $outcome_fe (agreement_count = agree_region_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label

xtivreg $outcome_fe (agreement_count = agree_subreg_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label
    
// Variation using outcome that is average of 3 future months of fatalities
xtivreg $outcome_future (agreement_count = agree_subreg_out_p${chosen_range}_wtrade) $controls_fe if year >= 1990 & year <= 2022 & (best_prevm>0 & best_prevm!=.), fe vce(cluster countryid)
outreg2 using "$HPresults/tables/regressions/regressions_iv/iv_results_2_`k'.xls", append excel bdec(3) sdec(3) slow(100) label


