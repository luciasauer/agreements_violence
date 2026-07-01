clear all
set more off
capture set maxvar 10000

* ── Set this once per machine ───────────────────────────────────────────────
global projroot "/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/1_agreements_violence/agreements_violence/"
* ────────────────────────────────────────────────────────────────────────────

global datapath "${projroot}data/output/conflict_level"
global outpath  "${projroot}src/3_causal_effect_estimation/3_0_csdid/results/hte"

capture mkdir "${projroot}src/3_causal_effect_estimation/3_0_csdid/results"
capture mkdir "${outpath}"

do "${projroot}src/3_causal_effect_estimation/3_0_csdid/helpers.do"


*==============================================================*
* 1. LOAD CONFLICT-LEVEL PROXIES
*    Produced by: src/5_survival_analysis/1_proxies_construction.ipynb
*    Run that notebook first — the last export cell creates this file.
*    One row per conflict; variable names shortened to fit Stata (<= 32 chars).
*==============================================================*
import delimited using "${datapath}/conflict_proxies.csv", clear
tempfile prx
save `prx'


*==============================================================*
* 2. LOAD QUARTERLY PANEL + MERGE PROXIES
*    Produced by: first_agreement_csdid.do (run that first).
*    yq exported as its underlying Stata quarterly integer.
*==============================================================*
import delimited using "${datapath}/conflict_panel_quarters.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

* yq is exported as a formatted string ("1989q1") by Stata's export delimited;
* convert it back to a Stata quarterly date integer.
gen yq_num = quarterly(yq, "YQ")
format yq_num %tq
drop yq
rename yq_num yq

merge m:1 conflict_id using `prx', keep(master match) nogenerate
xtset conflict_id yq, quarterly


*==============================================================*
* 3. DIAGNOSTIC: SAMPLE SIZES BY SUBGROUP
*==============================================================*
preserve
    bysort conflict_id: keep if _n == 1
    gen _treated = (gvar != 0)
    di _n "Treated vs. never-treated by IA type (high_ia_bin):"
    tab high_ia_bin _treated, row
restore


*==============================================================*
* 4. CSDID BY INFORMATION ASYMMETRY — NO COVARIATES
*    high_ia_bin = 1: experience_total == 0 (no prior fighting — high IA)
*    high_ia_bin = 0: experience_total >  0 (prior fighting    — low  IA)
*==============================================================*

* ── High IA ───────────────────────────────────────────────────────────────
preserve
    keep if high_ia_bin == 1

    csdid2 ln_deaths, ///
        ivar(conflict_id) time(yq) gvar(gvar) ///
        notyet method(drimp) cluster(conflict_id)

    estat event, window(-8 12) estore(ev_high_ia)
    csdid_plot, estname(ev_high_ia) suffix(hte_high_ia) ///
        xtitle("Quarters relative to first agreement")

    estimates restore ev_high_ia
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
    estimates store tbl_high_ia
restore

* ── Low IA ────────────────────────────────────────────────────────────────
preserve
    keep if high_ia_bin == 0

    csdid2 ln_deaths, ///
        ivar(conflict_id) time(yq) gvar(gvar) ///
        notyet method(drimp) cluster(conflict_id)

    estat event, window(-8 12) estore(ev_low_ia)
    csdid_plot, estname(ev_low_ia) suffix(hte_low_ia) ///
        xtitle("Quarters relative to first agreement")

    estimates restore ev_low_ia
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
    estimates store tbl_low_ia
restore


*==============================================================*
* 5. EXPORT LaTeX TABLE
*==============================================================*
local vl    varlabels(pre_avg "Pre-period average" post_avg "Post-period average")
local stars star(* 0.10 ** 0.05 *** 0.01)
local note  "Standard errors clustered at the conflict level in parentheses. High IA = no prior fighting experience (experience total = 0). Low IA = prior fighting experience exists. * p<0.10, ** p<0.05, *** p<0.01."

esttab tbl_high_ia tbl_low_ia ///
    using "${outpath}/table_hte_ia.tex", replace ///
    b(%9.3f) se(%9.3f) se `stars' `vl' ///
    mtitle("High IA" "Low IA") ///
    title("Effect of First Peace Agreement on ln(1 + Fatalities) by Information Asymmetry") ///
    noobs nonotes booktabs addnotes("`note'")
