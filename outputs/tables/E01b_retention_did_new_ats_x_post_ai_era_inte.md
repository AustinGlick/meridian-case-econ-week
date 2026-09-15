### E01b. Retention DiD: new ATS x post-AI-era interaction

| term                                          |   estimate |    se |   ci_low |   ci_high |     p |         n |   clusters |
|:----------------------------------------------|-----------:|------:|---------:|----------:|------:|----------:|-----------:|
| new ATS effect, pre-AI era (2021-22)          |      0.003 | 0.009 |   -0.015 |     0.020 | 0.772 | 41677.000 |     40.000 |
| DiD interaction: extra new-ATS effect, AI era |     -0.023 | 0.010 |   -0.042 |    -0.004 | 0.018 | 41677.000 |     40.000 |
| post-era gap, new vs legacy (sum of the two)  |     -0.021 | 0.009 |   -0.038 |    -0.004 | 0.017 | 41677.000 |     40.000 |

*Sample:* n=41677, 40 center clusters.
*Notes:* Outcome: retained_6mo (0/1, linear probability). FE: center, start_month; post_ai (application-month era) entered explicitly because start-month FE do not absorb it for hires who applied before and started after the cutoff. Controls: resume/license/experience/referral/employed/wage/unemployment. Cluster: center. Row 1 = new-ATS effect before the AI era; row 2 = the DiD interaction; row 3 = their sum, the new-vs-legacy gap in the AI era.
*Source:* analysis/02_retention_trend.py
