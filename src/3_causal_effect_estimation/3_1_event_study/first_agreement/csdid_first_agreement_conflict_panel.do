/*******************************************************************
Project: Peace Agreements Effect on Conflict Intensity
Author: Lucia Sauer
Date: 2025-12-17

Purpose:
Estimate the causal effect of peace agreements on conflict fatalities (log_best)
using Callaway & Sant'Anna's (2021) Difference-in-Differences estimator.
The dataset is a panel at conflict level that spans from 1989-01 to 2024-12

Treatment definition: 

References:
- Callaway & Sant'Anna (2021): "Difference-in-Differences with Multiple Time Periods"
*******************************************************************/


*Installation of csdid2 for long panels


*******************************************************************
* 1. Import dataset and preprocessing
*******************************************************************

clear all
set more off

import delimited ///
"/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/agreements_violence/data/output/conflict_level/conflict_panel.csv"


*******************************************************************
* 2.a Estimate causal effects (CSDID) Agreements
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

csdid2 log_best, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)

}


*******************************************************************
* 2.b Estimate causal effects (CSDID) (with controls)
*******************************************************************

* Controlling for conflict_age as year_mo - start_date, and duration_months as end_date - start_date
{
csdid2 log_best conflict_age duration_months, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}


* Controlling for the active_conflict_age as year_mo - start_date, and duration_months as end_date - start_date
{
csdid2 log_best real_observation conflict_age duration_months, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

* Controlling for the conflict_age as year_mo - start_date and duration_months as end_date - start_date + region + onset_year + current_month (monthly seasonality)
{
csdid2 log_best conflict_age duration_months i.region_main_num i.current_month i.start_year, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

* Controlling for the conflict_age as year_mo - start_date and duration_months as end_date - start_date + region 
{
csdid2 log_best conflict_age duration_months i.region_main_num, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}


* Controlling for the conflict_age as dummies 

{
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}
/*
------------------------------------------------------------------------------
             | Coefficient  Std. err.      z    P>|z|     [95% conf. interval]
-------------+----------------------------------------------------------------
     Pre_avg |  -.2718243   .3192359    -0.85   0.395    -.8975151    .3538666
    Post_avg |  -.6854091     .53572    -1.28   0.201    -1.735401    .3645827
*/


{
csdid2 log_best real_observation conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

* Controlling for the conflict_age as dummies + region 
{
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m i.region_main_num, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}


* Controlling for the conflict_age as dummies + onset_year 
{
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m i.start_year, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

* Controlling for the conflict_age as dummies +  current_month to control for seasonality (this doesnt change the results because it already account for that)
{
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m i.current_month, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}


* Controlling for the conflict_age as dummies + region + onset_year
{
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m i.region_main_num i.start_year, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

/*
------------------------------------------------------------------------------
             | Coefficient  Std. err.      z    P>|z|     [95% conf. interval]
-------------+----------------------------------------------------------------
     Pre_avg |    .033973   .5182843     0.07   0.948    -.9818456    1.049792
    Post_avg |  -.4815922   .5977119    -0.81   0.420    -1.653086    .6899017
*/




*******************************************************************
* 2.c Estimate causal effects (CSDID) (heterogeneity)
*******************************************************************


/*

Run results for treated conflicts with more than 1000 fatalities before 1° agreement (high_intensity=1)
*/

{
clear all
set more off

import delimited ///
"/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/peace_agreements_impulse_response/data/output/conflict_panel/conflict_panel_balanced_first_treatment_type1_18windows.csv"
	
keep if (treated_agreement == 0) | (high_intensity == 1)	
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}

/*

Run results for treated conflicts with less than 1000 fatalities before 1° agreement (high_intensity=0)
*/
{
clear all
set more off

import delimited ///
"/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/peace_agreements_impulse_response/data/output/conflict_panel/conflict_panel_balanced_first_treatment_type1_18windows.csv"

keep if (treated_agreement == 0) | (high_intensity == 0)	
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)	
}

*******************************************************************
* 2.d Estimate causal effects (CSDID) (aggregate bin lead/lags)
*******************************************************************

{
clear all
set more off

import delimited ///
"/Users/luciasauer/Library/CloudStorage/GoogleDrive-lucia.sauer@bse.eu/Mi unidad/EconAI/peace_agreements_impulse_response/data/output/conflict_panel/conflict_panel_balanced_first_treatment_type1_18windows.csv"
csdid2 log_best conflict_age_less_6m conflict_age_less_12m conflict_age_less_18m conflict_age_less_24m conflict_age_less_30m, ivar(conflict_id) tvar(year_mo_numeric) gvar(first_agreement_date) notyet method(dripw) cluster(isocode_main_num)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot	
}

estat event, window(-18 18) post

* Example syntax (adapted to your case):
matrix b = e(b)
matrix V = e(V)

* Select coef and elements from var and cov matrix
matrix b_clean = b[1, 1..36]
matrix V_clean = V[1..36, 1..36]

* Pre-lejano (-18 a -12)
lincom (1/7)*(_b[event__-18] + _b[event__-17] + _b[event__-16] + ///
              _b[event__-15] + _b[event__-14] + _b[event__-13] + _b[event__-12])

* Pre-cercano (-11 a -1)
lincom (1/11)*(_b[event__-11] + _b[event__-10] + _b[event__-9] + _b[event__-8] + ///
               _b[event__-7] + _b[event__-6] + _b[event__-5] + _b[event__-4] + ///
               _b[event__-3] + _b[event__-2] + _b[event__-1])

* Post-inmediato (0 a 5)
lincom (1/6)*(_b[event__0] + _b[event__1] + _b[event__2] + _b[event__3] + _b[event__4] + _b[event__5])

* Post-medio (6 a 12)
lincom (1/7)*(_b[event__6] + _b[event__7] + _b[event__8] + _b[event__9] + ///
              _b[event__10] + _b[event__11] + _b[event__12])

* Post-tardío (13 a 18)
lincom (1/6)*(_b[event__13] + _b[event__14] + _b[event__15] + ///
              _b[event__16] + _b[event__17] + _b[event__18])




*******************************************************************
* 2.e Estimate causal effects (CSDID) (several agreements)
*******************************************************************
{

csdid2 log_best, ivar(conflict_id_stacked) tvar(year_mo_numeric) gvar(group_var_agreement) notyet method(dripw) cluster(conflict_id)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)

}


*******************************************************************
* 2.d Estimate causal effects (CSDID) (several agreements w weights)
*******************************************************************
{
csdid2 log_best [pw=weight], ivar(conflict_id_stacked) tvar(year_mo_numeric) gvar(group_var_agreement) notyet method(dripw) cluster(conflict_id)
estat event, window(-18 18) wboot
estat event,  window(-18 18) wboot plot
csdid2_estat  event,  window(-18 18)
}
