clear all
set more off
capture set maxvar 10000

import delimited using "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level/conflict_panel.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

destring conflict_id best agreement ///
    start_year, replace force

*==============================================================*
* 1. MONTHLY -> QUARTERLY TIME + FIRST / SECOND AGREEMENT
*==============================================================*
gen year_num  = real(substr(year_mo, 1, 4))
gen month_num = real(substr(year_mo, 6, 2))
gen quarter   = ceil(month_num / 3)
gen yq        = yq(year_num, quarter)
format yq %tq

sort conflict_id year_num month_num
by conflict_id: gen cum_agree_monthly = sum(agreement)

gen first_agree_month  = (agreement == 1 & cum_agree_monthly == 1)

gen first_agree_yq = yq if first_agree_month == 1
by conflict_id: egen first_agreement_quarter = min(first_agree_yq)
format first_agreement_quarter %tq

by conflict_id: egen total_agreements = total(agreement)

*==============================================================*
* 2. COLLAPSE TO QUARTERLY
*==============================================================*
collapse (sum) best n_events                                       ///
         (max) agreement comp_agreement subs_agreement             ///
               first_agree_month                 ///
         (first) country region start_year start_date end_date     ///
                 first_agreement_quarter   ///
                 total_agreements                                  ///
         , by(conflict_id yq)

rename first_agree_month  first_agreement

gen ln_deaths = ln(best + 1)

xtset conflict_id yq, quarterly

*==============================================================*
* 3. CONVERT UCDP START / END DATES TO QUARTERS
*==============================================================*
gen start_year_num  = real(substr(start_date, 1, 4))
gen start_month_num = real(substr(start_date, 6, 2))
gen start_quarter   = ceil(start_month_num / 3)
gen start_yq        = yq(start_year_num, start_quarter)
format start_yq %tq

gen end_year_num  = real(substr(end_date, 1, 4))
gen end_month_num = real(substr(end_date, 6, 2))
gen end_quarter   = ceil(end_month_num / 3)
gen end_yq        = yq(end_year_num, end_quarter)
format end_yq %tq

*==============================================================*
* 4. EVENT TIME AT QUARTERLY LEVEL
*==============================================================*
gen event_time = yq - first_agreement_quarter if first_agreement_quarter != .

*==============================================================*
* 5. ACTIVITY THRESHOLD FOR TREATED UNITS
*==============================================================*
global activity_threshold = 12

sort conflict_id yq
by conflict_id: gen _lag1_b = best[_n-1]
by conflict_id: gen _lag2_b = best[_n-2]
gen deaths_prev2q = _lag1_b + _lag2_b
drop _lag1_b _lag2_b

gen _prev2_at_treat = deaths_prev2q if first_agreement == 1
bysort conflict_id: egen _conflict_prev2 = max(_prev2_at_treat)
drop _prev2_at_treat

gen _low_treat = (first_agreement_quarter != . & ///
    (_conflict_prev2 < $activity_threshold | _conflict_prev2 == .))

replace first_agreement_quarter = . if _low_treat == 1
replace first_agreement = 0 if _low_treat == 1
replace event_time = . if _low_treat == 1

*==============================================================*
* 6. CONTROL-SELECTION RULE
*==============================================================*
gen _inactive = (deaths_prev2q < $activity_threshold | deaths_prev2q == .)
gen _is_ctrl_period = (first_agreement_quarter == .) | ///
    (first_agreement_quarter != . & yq < first_agreement_quarter)
gen _drop_inactive = (_inactive == 1 & _is_ctrl_period == 1)

replace _drop_inactive = 0 if first_agreement == 1

drop if _drop_inactive == 1
drop _inactive _is_ctrl_period _drop_inactive

*==============================================================*
* 7. TRIM USING ORIGINAL UCDP CONFLICT WINDOW
*==============================================================*
drop if yq < start_yq & first_agreement != 1

gen _is_control_obs = (first_agreement_quarter == .) | ///
    (first_agreement_quarter != . & yq < first_agreement_quarter)

drop if yq > end_yq & _is_control_obs == 1 & first_agreement != 1
drop _is_control_obs

*==============================================================*
* 8. GVAR AT QUARTERLY LEVEL
*==============================================================*
gen gvar = first_agreement_quarter
replace gvar = 0 if gvar == .

*==============================================================*
* 9. CSDID AT QUARTERLY LEVEL
*==============================================================*
csdid2 ln_deaths, ///
    ivar(conflict_id) time(yq) gvar(gvar) ///
    notyet method(drimp)

estat event, window(-8 8) plot




clear all
set more off
capture set maxvar 10000

import delimited using "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/data/output/conflict_level/semester_sample_for_csdid.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear
	
csdid2 ln_deaths, ///
    ivar(conflict_id) time(ys) gvar(gvar) ///
    notyet method(drimp) cluster(conflict_id)

estat event, window(-4 6) plot


