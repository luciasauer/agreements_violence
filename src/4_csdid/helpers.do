*==============================================================*
* helpers.do
* Utility programs for the CSDID analysis.
* Called from first_agreement_csdid.do via:
*   do "${projroot}src/3_causal_effect_estimation/3_0_csdid/helpers.do"
* Requires: $outpath global to be set before calling csdid_plot.
*==============================================================*


* ── post_bV ──────────────────────────────────────────────────
* Posts global matrices b_mat and V_mat as e-class results so
* that estimates store works from a do-file context.
capture program drop post_bV
program define post_bV, eclass
    ereturn clear
    ereturn post b_mat V_mat
    ereturn local cmd "csdid_sum"
end


* ── csdid_plot ───────────────────────────────────────────────
* Draws a publication-ready event-study plot from a stored
* csdid2 estat event estimate.
*
* Required:
*   estname(str)  — name passed to estore() in estat event
*   suffix(str)   — filename suffix for the PNG output
*
* Optional:
*   xtitle(str)   — x-axis title (default: "Periods relative to first agreement")
*   ytitle(str)   — y-axis title (default: "ln(1 + Fatalities)")
*   precolor(str) — CI/dot color for pre-period,  as "R G B" (default: 44 110 138 = #2C6E8A)
*   postcolor(str)— CI/dot color for post-period, as "R G B" (default: 192 57 43  = #C0392B)
*
* Note: pass colors as RGB triplets "R G B" — Stata parses hex
*       (#RRGGBB) unreliably when expanded from a local macro.
capture program drop csdid_plot
program define csdid_plot
    version 17.0
    syntax, ESTNAME(string) SUFFIX(string) ///
            [PREcolor(string) POSTcolor(string) ///
             XTItle(string) YTItle(string)]

    if "`precolor'"  == "" local precolor  "44 110 138"
    if "`postcolor'" == "" local postcolor "192 57 43"
    if "`xtitle'"    == "" local xtitle    "Periods relative to first agreement"
    if "`ytitle'"    == "" local ytitle    "ATT on log(fatalities)"

    local outdir "${outpath}"
    if "`outdir'" == "" local outdir "`c(pwd)'"

    estimates restore `estname'
    matrix ev_b   = e(b)
    matrix ev_V   = e(V)
    local  cnames : colnames ev_b
    local  n      : word count `cnames'

    preserve
    clear
    quietly set obs `n'
    gen double t      = .
    gen double coef   = .
    gen double lo95   = .
    gen double hi95   = .
    gen        ispost = .

    local i 0
    foreach v of local cnames {
        local ++i
        if substr("`v'", 1, 2) == "tm" {
            quietly replace t      = -real(substr("`v'", 3, .)) in `i'
            quietly replace ispost = 0 in `i'
        }
        else if substr("`v'", 1, 2) == "tp" {
            quietly replace t      = real(substr("`v'", 3, .)) in `i'
            quietly replace ispost = 1 in `i'
        }
        local b_i  = ev_b[1, `i']
        local se_i = sqrt(ev_V[`i', `i'])
        quietly replace coef = `b_i'                   in `i'
        quietly replace lo95 = `b_i' - 1.96 * `se_i'  in `i'
        quietly replace hi95 = `b_i' + 1.96 * `se_i'  in `i'
    }
    sort t

    twoway ///
        (rcap lo95 hi95 t if ispost == 0, lcolor("`precolor'")  lwidth(thin)) ///
        (rcap lo95 hi95 t if ispost == 1, lcolor("`postcolor'") lwidth(thin)) ///
        (scatter coef t   if ispost == 0, mcolor("`precolor'")  msymbol(circle) msize(small)) ///
        (scatter coef t   if ispost == 1, mcolor("`postcolor'") msymbol(circle) msize(small)) ///
        , ///
        yline(0,    lcolor(gs8) lpattern(dash) lwidth(thin)) ///
        xline(0, lcolor(gs8) lpattern(dash) lwidth(thin)) ///
        legend(off) ///
        xtitle("`xtitle'") ytitle("`ytitle'") ///
        xlabel(, nogrid) ylabel(, nogrid) ///
        graphregion(color(white)) plotregion(color(white) margin(small))

    restore

    graph export "`outdir'/csdid_`suffix'.png", replace width(1200)
    di as txt "Saved: `outdir'/csdid_`suffix'.png"
end
