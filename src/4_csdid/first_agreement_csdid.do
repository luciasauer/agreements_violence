clear all
set more off
capture set maxvar 10000

* ── Set this once per machine ───────────────────────────────────────────────
global projroot "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/"
* ─────────────────────────────────────────────────────────────────────────────

global datapath "${projroot}data/output/conflict_level"
global outpath  "${projroot}src/4_csdid/results"

capture mkdir "${outpath}"

import delimited using "${datapath}/conflict_panel.csv", bindquote(strict) maxquotedrows(unlimited) clear

destring conflict_id best n_events ///
    agreement agreement_ged comp_agreement comp_agreement_ged ///
    subs_agreement subs_agreement_ged ///
    start_year, replace force


*==============================================================*
* 0. Helpers
*==============================================================*
do "${projroot}src/4_csdid/helpers.do"


*==============================================================*
* 1. MONTHLY -> QUARTERLY TIME + FIRST AGREEMENT
*==============================================================*
gen year_num  = real(substr(year_mo, 1, 4))
gen month_num = real(substr(year_mo, 6, 2))
gen quarter   = ceil(month_num / 3)
gen yq        = yq(year_num, quarter)
format yq %tq

sort conflict_id year_num month_num
by conflict_id: gen cum_agree_monthly = sum(agreement_ged)

gen first_agree_month  = (agreement_ged == 1 & cum_agree_monthly == 1)
gen second_agree_month = (agreement_ged == 1 & cum_agree_monthly == 2)

gen first_agree_yq = yq if first_agree_month == 1
by conflict_id: egen first_agreement_quarter = min(first_agree_yq)
format first_agreement_quarter %tq


*==============================================================*
* 2. COLLAPSE TO QUARTERLY
*==============================================================*
collapse (sum) best n_events                                             ///
         (max) agreement_ged comp_agreement_ged subs_agreement_ged       ///
               first_agree_month                                         ///
         (first) country region start_year start_date end_date           ///
                 first_agreement_quarter                                  ///
                 isocode_num isocode,                                    ///
         by(conflict_id yq)

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
*    fatalities in previous 2 quarters + current quarter >= 12
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

gen _best_at_treat = best if first_agreement == 1
bysort conflict_id: egen _conflict_best_at_treat = max(_best_at_treat)
drop _best_at_treat

* If _conflict_prev2 is missing, the agreement falls within the first 2 quarters
* of the conflict spell — deaths before the conflict's onset are 0 by definition.
replace _conflict_prev2 = 0 if _conflict_prev2 == .
gen _low_treat = (first_agreement_quarter != . & ///
    (_conflict_prev2 + _conflict_best_at_treat < $activity_threshold))

tab first_agreement

replace first_agreement_quarter = . if _low_treat == 1
replace first_agreement = 0 if _low_treat == 1
replace event_time = . if _low_treat == 1

tab first_agreement


*==============================================================*
* 6. CONTROL-SELECTION RULE
*    DROP INACTIVE OBSERVATIONS WHEN THEY ARE IN CONTROL RISK SET
*==============================================================*
gen _inactive = (deaths_prev2q < $activity_threshold | deaths_prev2q == .)
gen _is_ctrl_period = (first_agreement_quarter == .) | ///
    (first_agreement_quarter != . & yq < first_agreement_quarter)
gen _drop_inactive = (_inactive == 1 & _is_ctrl_period == 1)

* Keep actual treatment quarter even if deaths_prev2q missing there
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
* 9. ASSIGN PSEUDO-TREATMENT TIMING TO NEVER-TREATED
*    TO CONSTRUCT pre_violence_level AND age_at_treatment
*==============================================================*
preserve
keep if gvar != 0
bysort conflict_id: keep if _n == 1
sort conflict_id
keep conflict_id first_agreement_quarter
gen draw_id = _n
tempfile treat_quarters
save `treat_quarters', replace
count
local n_draws = r(N)
restore

preserve
keep if gvar == 0
bysort conflict_id: keep if _n == 1
keep conflict_id
set seed 20240315
gen double u = runiform()
gen draw_id = ceil(u * `n_draws')
replace draw_id = 1 if draw_id == 0
merge m:1 draw_id using `treat_quarters', keepusing(first_agreement_quarter) ///
    keep(master match) nogenerate
rename first_agreement_quarter pseudo_treat_q
tempfile pseudo_t
save `pseudo_t', replace
restore

merge m:1 conflict_id using `pseudo_t', keep(master match) nogenerate

gen pseudo_event_time = yq - pseudo_treat_q if gvar == 0 & pseudo_treat_q != .


*==============================================================*
* 10. CONSTRUCT pre_violence_level
*     TREATED: mean ln_deaths in t-4 to t-2 wrt actual treatment
*     CONTROLS: same wrt pseudo-treatment
*==============================================================*
gen help_level_t = ln_deaths if event_time >= -4 & event_time <= -2 & gvar != 0
gen help_level_c = ln_deaths if pseudo_event_time >= -4 & pseudo_event_time <= -2 & gvar == 0
gen help_level = help_level_t
replace help_level = help_level_c if gvar == 0

bysort conflict_id: egen pre_violence_level = mean(help_level)
drop help_level help_level_t help_level_c

* Fallback if missing
bysort conflict_id: egen tmp_mean_ln = mean(ln_deaths)
replace pre_violence_level = tmp_mean_ln if pre_violence_level == .
drop tmp_mean_ln


*==============================================================*
* 11. CONSTRUCT age_at_treatment
*     TREATED: actual treatment quarter - start_yq
*     CONTROLS: pseudo-treatment quarter - start_yq
*==============================================================*
gen age_at_treatment = first_agreement_quarter - start_yq if gvar != 0
replace age_at_treatment = pseudo_treat_q - start_yq if gvar == 0 & pseudo_treat_q != .

bysort conflict_id: egen age_tmp = mean(age_at_treatment)
drop age_at_treatment
rename age_tmp age_at_treatment
replace age_at_treatment = 0 if age_at_treatment == .

drop pseudo_event_time pseudo_treat_q

export delimited using "${datapath}/conflict_panel_quarters.csv", replace


*==============================================================*
* 12. CSDID AT QUARTERLY LEVEL
*     Each spec: plot → save PNG → lincom pre/post → store for table
*==============================================================*

* ── Spec 1: no covariates ────────────────────────────────────
csdid2 ln_deaths, ///
    ivar(conflict_id) time(yq) gvar(gvar) ///
    notyet method(drimp) cluster(conflict_id)

estat event, window(-8 12) estore(ev_qtr_nocov)
csdid_plot, estname(ev_qtr_nocov) suffix(event_qtr_nocov) ///
    xtitle("Quarters relative to first agreement")

estimates restore ev_qtr_nocov
lincom (tm8+tm7+tm6+tm5+tm4+tm3+tm2)/7
    scalar _pre_b  = r(estimate)
    scalar _pre_se = r(se)
lincom (tp0+tp1+tp2+tp3+tp4+tp5+tp6+tp7+tp8+tp9+tp10+tp11+tp12)/13
    scalar _post_b  = r(estimate)
    scalar _post_se = r(se)

matrix b_mat = (_pre_b, _post_b)
matrix V_mat = (_pre_se^2, 0 \ 0, _post_se^2)
matrix colnames b_mat = pre_avg post_avg
matrix colnames V_mat = pre_avg post_avg
matrix rownames V_mat = pre_avg post_avg
post_bV
estimates store tbl_qtr_nocov

* ── Spec 2: with covariates ──────────────────────────────────
csdid2 ln_deaths pre_violence_level age_at_treatment, ///
    ivar(conflict_id) time(yq) gvar(gvar) ///
    notyet method(drimp) cluster(conflict_id)

estat event, window(-8 12) estore(ev_qtr_cov)
csdid_plot, estname(ev_qtr_cov) suffix(event_qtr_cov) ///
    xtitle("Quarters relative to first agreement")

estimates restore ev_qtr_cov
lincom (tm8+tm7+tm6+tm5+tm4+tm3+tm2)/7
    scalar _pre_b  = r(estimate)
    scalar _pre_se = r(se)
lincom (tp0+tp1+tp2+tp3+tp4+tp5+tp6+tp7+tp8+tp9+tp10+tp11+tp12)/13
    scalar _post_b  = r(estimate)
    scalar _post_se = r(se)

matrix b_mat = (_pre_b, _post_b)
matrix V_mat = (_pre_se^2, 0 \ 0, _post_se^2)
matrix colnames b_mat = pre_avg post_avg
matrix colnames V_mat = pre_avg post_avg
matrix rownames V_mat = pre_avg post_avg
post_bV
estimates store tbl_qtr_cov


*==============================================================*
* 13. CONVERT QUARTERLY FILTERED SAMPLE TO SEMI-ANNUAL
*==============================================================*
gen half = ceil(quarter(dofq(yq)) / 2)
gen year_for_half = year(dofq(yq))
gen yh = (year_for_half - 1989) * 2 + half

gen first_agree_yh = .
replace first_agree_yh = (year(dofq(first_agreement_quarter)) - 1989) * 2 ///
    + ceil(quarter(dofq(first_agreement_quarter)) / 2) ///
    if first_agreement_quarter != .

bysort conflict_id: egen first_agreement_half = min(first_agree_yh)
drop first_agree_yh

gen gvar_sa = first_agreement_half
replace gvar_sa = 0 if gvar_sa == .

collapse (sum) best ///
         (firstnm) gvar_sa first_agreement_half first_agreement_quarter ///
                   start_yq pre_violence_level age_at_treatment         ///
                   isocode_num isocode country,                         ///
         by(conflict_id yh)

gen ln_deaths_sa = ln(best + 1)
xtset conflict_id yh

export delimited using "${datapath}/conflict_panel_semesters.csv", replace

* Diagnostics
preserve
bysort conflict_id: keep if _n == 1
count
local n_conf_sa = r(N)
count if gvar_sa != 0
local n_treat_sa = r(N)
count if gvar_sa == 0
local n_ctrl_sa = r(N)
restore

di _n "FINAL SEMI-ANNUAL ESTIMATION SAMPLE"
di "  Total conflicts:    `n_conf_sa'"
di "  Treated conflicts:  `n_treat_sa'"
di "  gvar_sa==0 units:   `n_ctrl_sa'"


*==============================================================*
* 14. CSDID AT SEMI-ANNUAL LEVEL
*     Each spec: plot → save PNG → lincom pre/post → store for table
*==============================================================*

* ── Spec 1: no covariates ────────────────────────────────────
csdid2 ln_deaths_sa, ///
    ivar(conflict_id) time(yh) gvar(gvar_sa) ///
    notyet method(drimp) cluster(conflict_id)

estat event, window(-4 6) estore(ev_sa_nocov)
csdid_plot, estname(ev_sa_nocov) suffix(event_sa_nocov) ///
    xtitle("Semesters relative to first agreement")

estimates restore ev_sa_nocov
lincom (tm4+tm3+tm2)/3
    scalar _pre_b  = r(estimate)
    scalar _pre_se = r(se)
lincom (tp0+tp1+tp2+tp3+tp4+tp5+tp6)/7
    scalar _post_b  = r(estimate)
    scalar _post_se = r(se)

matrix b_mat = (_pre_b, _post_b)
matrix V_mat = (_pre_se^2, 0 \ 0, _post_se^2)
matrix colnames b_mat = pre_avg post_avg
matrix colnames V_mat = pre_avg post_avg
matrix rownames V_mat = pre_avg post_avg
post_bV
estimates store tbl_sa_nocov

* ── Spec 2: with covariates ──────────────────────────────────
csdid2 ln_deaths_sa pre_violence_level age_at_treatment, ///
    ivar(conflict_id) time(yh) gvar(gvar_sa) ///
    notyet method(drimp) cluster(conflict_id)

estat event, window(-4 6) estore(ev_sa_cov)
csdid_plot, estname(ev_sa_cov) suffix(event_sa_cov) ///
    xtitle("Semesters relative to first agreement")

estimates restore ev_sa_cov
lincom (tm4+tm3+tm2)/3
    scalar _pre_b  = r(estimate)
    scalar _pre_se = r(se)
lincom (tp0+tp1+tp2+tp3+tp4+tp5+tp6)/7
    scalar _post_b  = r(estimate)
    scalar _post_se = r(se)

matrix b_mat = (_pre_b, _post_b)
matrix V_mat = (_pre_se^2, 0 \ 0, _post_se^2)
matrix colnames b_mat = pre_avg post_avg
matrix colnames V_mat = pre_avg post_avg
matrix rownames V_mat = pre_avg post_avg
post_bV
estimates store tbl_sa_cov


*==============================================================*
* 15. EXPORT LATEX TABLES
*==============================================================*
local vl     varlabels(pre_avg "Pre-period average" post_avg "Post-period average")
local stars  star(* 0.10 ** 0.05 *** 0.01)
local note   "Standard errors clustered at the conflict level in parentheses. * p<0.10, ** p<0.05, *** p<0.01."

esttab tbl_qtr_nocov tbl_qtr_cov ///
    using "${outpath}/table_csdid_quarterly.tex", replace ///
    b(%9.3f) se(%9.3f) se `stars' `vl' ///
    mtitle("No covariates" "Covariates") ///
    title("Effect of First Peace Agreement on ln(1 + Fatalities): Quarterly Panel") ///
    noobs nonotes booktabs addnotes("`note'")

esttab tbl_sa_nocov tbl_sa_cov ///
    using "${outpath}/table_csdid_semiannual.tex", replace ///
    b(%9.3f) se(%9.3f) se `stars' `vl' ///
    mtitle("No covariates" "Covariates") ///
    title("Effect of First Peace Agreement on ln(1 + Fatalities): Semi-annual Panel") ///
    noobs nonotes booktabs addnotes("`note'")
