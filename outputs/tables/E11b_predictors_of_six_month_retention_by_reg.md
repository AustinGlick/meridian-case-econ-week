### E11b. Predictors of six-month retention, by regime

|    | regime      | predictor            |   estimate |    se |   ci_low |   ci_high |     n |   clusters |
|---:|:------------|:---------------------|-----------:|------:|---------:|----------:|------:|-----------:|
|  0 | legacy_pre  | essay_rubric_score   |      0.008 | 0.001 |    0.006 |     0.010 | 13040 |         40 |
|  1 | legacy_pre  | resume_score         |      0.010 | 0.003 |    0.005 |     0.015 | 13040 |         40 |
|  2 | legacy_pre  | has_adjuster_license |      0.016 | 0.006 |    0.005 |     0.027 | 13040 |         40 |
|  3 | legacy_pre  | prior_claims_years   |      0.004 | 0.001 |    0.001 |     0.006 | 13040 |         40 |
|  4 | legacy_pre  | referral             |      0.016 | 0.005 |    0.005 |     0.026 | 13040 |         40 |
|  5 | legacy_pre  | interview_score      |      0.009 | 0.004 |   -0.000 |     0.017 | 13040 |         40 |
|  6 | legacy_post | essay_rubric_score   |      0.005 | 0.002 |    0.002 |     0.008 |  6326 |         28 |
|  7 | legacy_post | resume_score         |      0.012 | 0.004 |    0.004 |     0.020 |  6326 |         28 |
|  8 | legacy_post | has_adjuster_license |      0.045 | 0.008 |    0.030 |     0.061 |  6326 |         28 |
|  9 | legacy_post | prior_claims_years   |      0.008 | 0.002 |    0.004 |     0.011 |  6326 |         28 |
| 10 | legacy_post | referral             |      0.024 | 0.008 |    0.009 |     0.039 |  6326 |         28 |
| 11 | legacy_post | interview_score      |      0.027 | 0.008 |    0.011 |     0.043 |  6326 |         28 |
| 12 | new_pre     | essay_rubric_score   |      0.011 | 0.002 |    0.007 |     0.014 |  5920 |         12 |
| 13 | new_pre     | resume_score         |      0.009 | 0.002 |    0.005 |     0.014 |  5920 |         12 |
| 14 | new_pre     | has_adjuster_license |      0.028 | 0.010 |    0.008 |     0.048 |  5920 |         12 |
| 15 | new_pre     | prior_claims_years   |      0.005 | 0.003 |   -0.001 |     0.010 |  5920 |         12 |
| 16 | new_pre     | referral             |      0.017 | 0.008 |    0.001 |     0.033 |  5920 |         12 |
| 17 | new_pre     | interview_score      |      0.018 | 0.007 |    0.003 |     0.032 |  5920 |         12 |
| 18 | new_post    | essay_rubric_score   |     -0.001 | 0.001 |   -0.004 |     0.001 | 16391 |         33 |
| 19 | new_post    | resume_score         |      0.019 | 0.003 |    0.013 |     0.025 | 16391 |         33 |
| 20 | new_post    | has_adjuster_license |      0.049 | 0.005 |    0.039 |     0.059 | 16391 |         33 |
| 21 | new_post    | prior_claims_years   |      0.005 | 0.002 |    0.002 |     0.008 | 16391 |         33 |
| 22 | new_post    | referral             |      0.032 | 0.006 |    0.021 |     0.044 | 16391 |         33 |
| 23 | new_post    | interview_score      |      0.027 | 0.004 |    0.019 |     0.035 | 16391 |         33 |

*Sample:* 41,677 hires with an observed outcome, split into four ATS x era cells.
*Notes:* Outcome: retained_6mo (linear probability). FE: center, start_month. Cluster: center. Each cell is a separate regression on its subsample; all six predictors enter together.
*Source:* analysis/05_screen_components.py
