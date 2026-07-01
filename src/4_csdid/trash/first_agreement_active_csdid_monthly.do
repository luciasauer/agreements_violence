clear all
set more off
capture set maxvar 10000

import delimited using "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level/conflict_panel.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

destring conflict_id best n_events agreement comp_agreement subs_agreement ///
    start_year, replace force

*==============================================================*
* 1. MONTHLY TIME + FIRST / SECOND AGREEMENT AT MONTH LEVEL
*==============================================================*
gen year_num  = real(substr(year_mo, 1, 4))
gen month_num = real(substr(year_mo, 6, 2))

* monthly Stata date
gen ym_date = ym(year_num, month_num)
format ym_date %tm

sort conflict_id year_num month_num
by conflict_id: gen cum_agree_monthly = sum(agreement)

gen first_agreement  = (agreement == 1 & cum_agree_monthly == 1)

gen first_agree_ym = ym_date if first_agreement == 1
by conflict_id: egen first_agreement_month = min(first_agree_ym)
format first_agreement_month %tm

by conflict_id: egen total_agreements = total(agreement)

gen ln_deaths = ln(best + 1)

xtset conflict_id ym_date, monthly

*==============================================================*
* 2. CONVERT UCDP START / END DATES TO MONTHS
*==============================================================*
gen start_year_num  = real(substr(start_date, 1, 4))
gen start_month_num = real(substr(start_date, 6, 2))
gen start_ym        = ym(start_year_num, start_month_num)
format start_ym %tm

gen end_year_num  = real(substr(end_date, 1, 4))
gen end_month_num = real(substr(end_date, 6, 2))
gen end_ym        = ym(end_year_num, end_month_num)
format end_ym %tm

*==============================================================*
* 3. EVENT TIME AT MONTHLY LEVEL
*==============================================================*
gen event_time = ym_date - first_agreement_month if first_agreement_month != .

*==============================================================*
* 4. ACTIVITY THRESHOLD FOR TREATED UNITS
*    MONTHLY VERSION OF THE QUARTERLY FILTER:
*    SAME THRESHOLD (12), OVER PREVIOUS 6 MONTHS
*==============================================================*
global activity_threshold = 12

sort conflict_id ym_date
by conflict_id: gen _lag1_b = best[_n-1]
by conflict_id: gen _lag2_b = best[_n-2]
by conflict_id: gen _lag3_b = best[_n-3]
by conflict_id: gen _lag4_b = best[_n-4]
by conflict_id: gen _lag5_b = best[_n-5]
by conflict_id: gen _lag6_b = best[_n-6]

egen deaths_prev6m = rowtotal(_lag1_b _lag2_b _lag3_b _lag4_b _lag5_b _lag6_b)
drop _lag1_b _lag2_b _lag3_b _lag4_b _lag5_b _lag6_b

gen _prev6_at_treat = deaths_prev6m if first_agreement == 1
bysort conflict_id: egen _conflict_prev6 = max(_prev6_at_treat)
drop _prev6_at_treat

gen _low_treat = (first_agreement_month != . & ///
    (_conflict_prev6 < $activity_threshold | _conflict_prev6 == .))

replace first_agreement_month = . if _low_treat == 1
replace first_agreement = 0 if _low_treat == 1
replace event_time = . if _low_treat == 1

*==============================================================*
* 5. CONTROL-SELECTION RULE
*    DROP INACTIVE OBSERVATIONS WHEN THEY ARE IN CONTROL RISK SET
*==============================================================*
gen _inactive = (deaths_prev6m < $activity_threshold | deaths_prev6m == .)

gen _is_ctrl_period = (first_agreement_month == .) | ///
    (first_agreement_month != . & ym_date < first_agreement_month)

gen _drop_inactive = (_inactive == 1 & _is_ctrl_period == 1)

* keep the actual treatment month even if lag window is missing there
replace _drop_inactive = 0 if first_agreement == 1

drop if _drop_inactive == 1
drop _inactive _is_ctrl_period _drop_inactive

*==============================================================*
* 6. TRIM USING ORIGINAL UCDP CONFLICT WINDOW
*==============================================================*
drop if ym_date < start_ym & first_agreement != 1

gen _is_control_obs = (first_agreement_month == .) | ///
    (first_agreement_month != . & ym_date < first_agreement_month)

drop if ym_date > end_ym & _is_control_obs == 1 & first_agreement != 1
drop _is_control_obs

*==============================================================*
* 7. GVAR AT MONTHLY LEVEL
*==============================================================*
gen gvar = first_agreement_month
replace gvar = 0 if gvar == .

*==============================================================*
* 8. CSDID AT MONTHLY LEVEL - NO COVARIATES
*==============================================================*
csdid2 ln_deaths, ///
    ivar(conflict_id) time(ym_date) gvar(gvar) ///
    notyet method(drimp)

estat event, window(-18 18) plot
