first_ceasefire_agreement_mentions

Synthetic Difference-in-Differences Estimator

-----------------------------------------------------------------------------
    log_best |     ATT     Std. Err.     t      P>|t|    [95% Conf. Interval]
-------------+---------------------------------------------------------------
           D |  -0.88381    0.10916    -8.10    0.000    -1.09777    -0.66986
-----------------------------------------------------------------------------
95% CIs and p-values are based on large-sample approximations.
Refer to Arkhangelsky et al., (2021) for theoretical derivations.

first_agreement

 
Synthetic Difference-in-Differences Estimator

-----------------------------------------------------------------------------
    log_best |     ATT     Std. Err.     t      P>|t|    [95% Conf. Interval]
-------------+---------------------------------------------------------------
           D |  -0.89118    0.11048    -8.07    0.000    -1.10772    -0.67465
-----------------------------------------------------------------------------
95% CIs and p-values are based on large-sample approximations.
Refer to Arkhangelsky et al., (2021) for theoretical derivations.


. sdid_event log_best conflict_id year_mo_numeric D, effects(6) placebo(6) vce(placebo) brep(20)
Synthetic Difference-in-differences

Boostrap replications (20), placebo mode.
|0% ----------------------------------------- 100%|
|....................|


             |  Estimate         SE      LB CI      UB CI  Switchers 
-------------+------------------------------------------------------
         ATT | -.8911804   .1249505  -1.136083  -.6462774         71 
    Effect_1 |  .6571796   .0709014   .5182128   .7961463         71 
    Effect_2 |  .4279233   .0919411   .2477187   .6081278         71 
    Effect_3 |   .507202   .0816599   .3471487   .6672554         71 
    Effect_4 |  .5683478   .0793134   .4128936    .723802         71 
    Effect_5 |  .4220537   .0938083   .2381894   .6059179         71 
    Effect_6 |  .5040001   .0899022   .3277918   .6802084         71 
   Placebo_1 |  .3265864   .0848489   .1602824   .4928903         71 
   Placebo_2 |  .5486225   .0780006   .3957412   .7015038         71 
   Placebo_3 |  .3651924   .0810989   .2062385   .5241463         71 
   Placebo_4 |  .1586076   .1071258   -.051359   .3685743         71 
   Placebo_5 |  .1733569   .0823544   .0119423   .3347715         71 
   Placebo_6 | -.1339533   .0667441  -.2647717  -.0031349         71 

. 
end of do-file
