### E08b. Objective applicant attributes: new ATS x post-AI-era DiD

| outcome                 | term                                          |   estimate |    se |   ci_low |   ci_high |     p |      n |   clusters |
|:------------------------|:----------------------------------------------|-----------:|------:|---------:|----------:|------:|-------:|-----------:|
| resume_score            | new ATS effect, pre-AI era (2021-22)          |     -0.003 | 0.006 |   -0.015 |     0.008 | 0.559 | 529302 |         40 |
| resume_score            | DiD interaction: extra new-ATS effect, AI era |     -0.010 | 0.006 |   -0.021 |     0.001 | 0.078 | 529302 |         40 |
| resume_score            | post-era gap, new vs legacy (sum of the two)  |     -0.013 | 0.007 |   -0.027 |     0.000 | 0.057 | 529302 |         40 |
| has_adjuster_license    | new ATS effect, pre-AI era (2021-22)          |     -0.000 | 0.003 |   -0.006 |     0.006 | 0.916 | 529302 |         40 |
| has_adjuster_license    | DiD interaction: extra new-ATS effect, AI era |     -0.026 | 0.004 |   -0.035 |    -0.018 | 0.000 | 529302 |         40 |
| has_adjuster_license    | post-era gap, new vs legacy (sum of the two)  |     -0.026 | 0.004 |   -0.034 |    -0.019 | 0.000 | 529302 |         40 |
| prior_claims_experience | new ATS effect, pre-AI era (2021-22)          |      0.001 | 0.002 |   -0.004 |     0.005 | 0.715 | 529302 |         40 |
| prior_claims_experience | DiD interaction: extra new-ATS effect, AI era |     -0.024 | 0.004 |   -0.032 |    -0.015 | 0.000 | 529302 |         40 |
| prior_claims_experience | post-era gap, new vs legacy (sum of the two)  |     -0.023 | 0.004 |   -0.030 |    -0.016 | 0.000 | 529302 |         40 |
| prior_claims_years      | new ATS effect, pre-AI era (2021-22)          |     -0.006 | 0.009 |   -0.024 |     0.011 | 0.469 | 529302 |         40 |
| prior_claims_years      | DiD interaction: extra new-ATS effect, AI era |     -0.053 | 0.013 |   -0.078 |    -0.028 | 0.000 | 529302 |         40 |
| prior_claims_years      | post-era gap, new vs legacy (sum of the two)  |     -0.060 | 0.011 |   -0.080 |    -0.039 | 0.000 | 529302 |         40 |
| referral                | new ATS effect, pre-AI era (2021-22)          |     -0.004 | 0.002 |   -0.007 |    -0.000 | 0.043 | 529302 |         40 |
| referral                | DiD interaction: extra new-ATS effect, AI era |     -0.011 | 0.003 |   -0.017 |    -0.006 | 0.000 | 529302 |         40 |
| referral                | post-era gap, new vs legacy (sum of the two)  |     -0.015 | 0.003 |   -0.021 |    -0.009 | 0.000 | 529302 |         40 |
| currently_employed      | new ATS effect, pre-AI era (2021-22)          |      0.003 | 0.003 |   -0.003 |     0.009 | 0.342 | 529302 |         40 |
| currently_employed      | DiD interaction: extra new-ATS effect, AI era |     -0.021 | 0.003 |   -0.027 |    -0.015 | 0.000 | 529302 |         40 |
| currently_employed      | post-era gap, new vs legacy (sum of the two)  |     -0.018 | 0.004 |   -0.025 |    -0.011 | 0.000 | 529302 |         40 |

*Sample:* n=529,302 reviewed applications, 40 center clusters.
*Notes:* Each outcome regressed on treated_app + treated_app:post_ai with center and application-month FE, cluster center. Compare with the essay-score DiD in E06c.
*Source:* analysis/03_pool_quality.py
