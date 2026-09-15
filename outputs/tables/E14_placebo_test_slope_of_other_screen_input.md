### E14. Placebo test: slope of other screen inputs on six-month retention, by regime

|    | regime      |   estimate |    se |   ci_low |   ci_high | variable             |
|---:|:------------|-----------:|------:|---------:|----------:|:---------------------|
|  0 | legacy_pre  |      0.009 | 0.003 |    0.004 |     0.014 | resume_score         |
|  1 | legacy_post |      0.012 | 0.004 |    0.003 |     0.020 | resume_score         |
|  2 | new_pre     |      0.008 | 0.002 |    0.003 |     0.013 | resume_score         |
|  3 | new_post    |      0.023 | 0.003 |    0.017 |     0.028 | resume_score         |
|  4 | legacy_pre  |      0.020 | 0.006 |    0.009 |     0.030 | has_adjuster_license |
|  5 | legacy_post |      0.050 | 0.009 |    0.033 |     0.066 | has_adjuster_license |
|  6 | new_pre     |      0.033 | 0.010 |    0.014 |     0.052 | has_adjuster_license |
|  7 | new_post    |      0.060 | 0.005 |    0.050 |     0.071 | has_adjuster_license |
|  8 | legacy_pre  |      0.004 | 0.001 |    0.001 |     0.007 | prior_claims_years   |
|  9 | legacy_post |      0.009 | 0.002 |    0.005 |     0.012 | prior_claims_years   |
| 10 | new_pre     |      0.005 | 0.003 |    0.000 |     0.011 | prior_claims_years   |
| 11 | new_post    |      0.008 | 0.002 |    0.005 |     0.011 | prior_claims_years   |
| 12 | legacy_pre  |     -0.005 | 0.004 |   -0.013 |     0.004 | interview_score      |
| 13 | legacy_post |      0.019 | 0.008 |    0.003 |     0.035 | interview_score      |
| 14 | new_pre     |      0.001 | 0.007 |   -0.013 |     0.014 | interview_score      |
| 15 | new_post    |      0.032 | 0.004 |    0.024 |     0.040 | interview_score      |

*Sample:* 41,677 hires with an observed outcome (interview_score restricted to applicants who were interviewed).
*Notes:* Univariate slopes (each input alone) with center + start-month FE, cluster center. If these are stable while the essay's slope collapses (E12b), the essay result is not an artifact of a center-wide shift in hiring quality or measurement. E11b gives the multivariate version.
*Source:* analysis/06_essay_validity.py
