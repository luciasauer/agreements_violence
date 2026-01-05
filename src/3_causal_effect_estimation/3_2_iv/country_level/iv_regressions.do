/* -------------------------------------------------------------- */
/* AGREEMENTS AND VIOLENCE - COUNTRY PANEL                         */
/* FE + IV (xtivreg) and First Stage (xtreg)                       */
/* Author: Lucia Sauer                                             */
/* Last update: 2026-01-05                                         */
/* Treatment (endog): ceasefire_agreements_mentions (0/1)          */
/* -------------------------------------------------------------- */

clear all                                       /* -------------------------------------------------------------- */
/* AGREEMENTS AND VIOLENCE - COUNTRY PANEL                         */
/* FE + IV (xtivreg) and First Stage (xtreg)                       */
/* Author: Lucia Sauer                                             */
/* Last update: 2026-01-05                                         */
/* Treatment (endog): ceasefire_agreements_mentions (0/1)          */
/* -------------------------------------------------------------- */

clear all
set more off
set linesize 120

*******************************************************************
* 0. Paths + load data
*******************************************************************
local treatment "ceasfire_agreements_mentions"

local indir  "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/country_level"
local outdir "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/src/4_results/iv_regressions"

cap mkdir "`outdir'"

import delimited "`indir'/country_panel.csv", clear

*******************************************************************
* 1. Panel setup
*******************************************************************
egen countryid = group(isocode_num)
xtset countryid year_mo_numeric
sort countryid year_mo_numeric


*******************************************************************
* 2. Define outcome + controls
*******************************************************************

local y "log_best"

*gen fatalities in previous month (we filter for this in two of the models later)
rangestat (mean) best_prevm=best, interval(year_mo_numeric -1 -1) by(isocode_num)

* 6 lags of outcome as controls
forvalues i = 1/6 {
    gen L`i'_`y' = L`i'.`y'
}
local controls "L1_`y' L2_`y' L3_`y' L4_`y' L5_`y' L6_`y'"

* Sample window (edit if needed)
local tmin 1990
local tmax 2024

*******************************************************************
* 3. Output files
*******************************************************************
local fs_out "`outdir'/first_stage_`treatment'.xls"
local iv_out "`outdir'/iv_2sls_`treatment'.xls"

cap erase "`fs_out'"
cap erase "`iv_out'"

*******************************************************************
* 4. INSTRUMENT SET 1: Regional/Subregional spillovers (monthly)
*******************************************************************
* Instruments
local z1 "agree_region_excl_w_trade"
local z2 "agree_subreg_excl_w_trade"
local z3 "agree_region_excl_w_dist"
local z4 "agree_subreg_excl_w_dist"

* FIRST STAGE + IV for z1

xtreg `treatment' `z1' `controls' if year>=`tmin' & year<=`tmax' & influence > 0, fe vce(cluster countryid)
test `z1'
outreg2 using "`fs_out'", replace excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","`z1'","Set","1")

xtivreg `y' (`treatment' = `z1') `controls' if year>=`tmin' & year<=`tmax' & influence > 0 & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", replace excel bdec(3) sdec(3) label ///
	addtext("Instrument","`z1'","Set","1","Endog","`treatment'","Outcome","`y'")

* FIRST STAGE + IV for z2

xtreg `treatment' `z2' `controls' if year>=`tmin' & year<=`tmax' & influence > 0, fe vce(cluster countryid)
test `z2'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","`z2'","Set","1")

xtivreg `y' (`treatment' = `z2') `controls' if year>=`tmin' & year<=`tmax' & influence > 0 & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","`z2'","Set","1","Endog","`treatment'","Outcome","`y'")


* FIRST STAGE + IV for z3
	
xtreg `treatment' `z3' `controls' if year>=`tmin' & year<=`tmax' & influence > 0, fe vce(cluster countryid)
test `z3'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","`z3'","Set","1")

xtivreg `y' (`treatment' = `z3') `controls' if year>=`tmin' & year<=`tmax' & influence > 0 & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","`z3'","Set","1","Endog","`treatment'","Outcome","`y'")

* FIRST STAGE + IV for z4
	
xtreg `treatment' `z4' `controls' if year>=`tmin' & year<=`tmax' & influence > 0, fe vce(cluster countryid)
test `z4'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","`z4'","Set","1")

xtivreg `y' (`treatment' = `z4') `controls' if year>=`tmin' & year<=`tmax' & influence > 0 & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","`z4'","Set","1","Endog","`treatment'","Outcome","`y'")


	
*******************************************************************
* 5. INSTRUMENT SET 2: UN-SC influence (often annual -> lag 12 months)
*******************************************************************
local z5 "influence_veto"
local z6 "influence_gdp"
local z7 "influence_log_gdp"
local z8 "influence"

* Create 12-month lags if available
foreach v in `z5' `z6' `z7' `z8' {
    gen L12_`v' = L12.`v'
}

* Use lagged versions
* L12_influence_veto
xtreg `treatment' L12_`z5' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z5'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z5'","Set","2")

xtivreg `y' (`treatment' = L12_`z5') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z5'","Set","2","Endog","`treatment'","Outcome","`y'")


* L12_influence_gdp
xtreg `treatment' L12_`z6' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z6'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z6'","Set","2")

xtivreg `y' (`treatment' = L12_`z6') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z6'","Set","2","Endog","`treatment'","Outcome","`y'")


* L12_influence_log_gdp
xtreg `treatment' L12_`z7' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z7'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z7'","Set","2")

xtivreg `y' (`treatment' = L12_`z7') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z7'","Set","2","Endog","`treatment'","Outcome","`y'")


* L12_influence
xtreg `treatment' L12_`z8' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z8'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z8'","Set","2")

xtivreg `y' (`treatment' = L12_`z8') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z8'","Set","2","Endog","`treatment'","Outcome","`y'")

*******************************************************************
* 6. INSTRUMENT SET 3: SC attention elsewhere (lag 12 months)
*******************************************************************
local z9  "sc_at_war_outside_isocode"
local z10 "sc_at_war_outside_sub_region"
local z11 "sc_at_war_outside_region"

foreach v in `z9' `z10' `z11' {
    gen L12_`v' = L12.`v'
}

* L12_sc_at_war_outside_isocode

xtreg `treatment' L12_`z9' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z9'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z9'","Set","3")

xtivreg `y' (`treatment' = L12_`z9') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z9'","Set","3","Endog","`treatment'","Outcome","`y'")


* L12_sc_at_war_outside_sub_region

xtreg `treatment' L12_`z10' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z10'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z10'","Set","3")

xtivreg `y' (`treatment' = L12_`z10') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z10'","Set","3","Endog","`treatment'","Outcome","`y'")


* L12_sc_at_war_outside_region

xtreg `treatment' L12_`z11' `controls' if year>=`tmin' & year<=`tmax', fe vce(cluster countryid)
test L12_`z11'
outreg2 using "`fs_out'", append excel bdec(3) sdec(3) label addstat("F-stat", r(F)) ///
	addtext("Instrument","L12_`z11'","Set","3")

xtivreg `y' (`treatment' = L12_`z11') `controls' if year>=`tmin' & year<=`tmax' & best_prevm>0, fe vce(cluster countryid)
outreg2 using "`iv_out'", append excel bdec(3) sdec(3) label ///
	addtext("Instrument","L12_`z11'","Set","3","Endog","`treatment'","Outcome","`y'")


di as result "Done."
di as result "First-stage table: `fs_out'"
di as result "IV results table:  `iv_out'"
