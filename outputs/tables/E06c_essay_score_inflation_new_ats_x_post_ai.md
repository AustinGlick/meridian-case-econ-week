### E06c. Essay-score inflation: new ATS x post-AI-era interaction

| term                                          |   estimate |    se |   ci_low |   ci_high |     p |          n |   clusters |
|:----------------------------------------------|-----------:|------:|---------:|----------:|------:|-----------:|-----------:|
| new ATS effect, pre-AI era (2021-22)          |      0.893 | 0.033 |    0.828 |     0.958 | 0.000 | 529302.000 |     40.000 |
| DiD interaction: extra new-ATS effect, AI era |      0.787 | 0.108 |    0.575 |     1.000 | 0.000 | 529302.000 |     40.000 |
| post-era gap, new vs legacy (sum of the two)  |      1.680 | 0.114 |    1.457 |     1.903 | 0.000 | 529302.000 |     40.000 |

*Sample:* n=529302, 40 center clusters.
*Notes:* Outcome: essay_rubric_score (0-30). Controls: resume/license/experience/referral/employed. FE: center, application_month. Cluster: center.
*Source:* analysis/03_pool_quality.py
