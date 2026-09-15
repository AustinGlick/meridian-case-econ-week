### E02b. Reopen-rate DiD: new ATS x post-AI-era interaction

| term                                          |   estimate |    se |   ci_low |   ci_high |     p |         n |   clusters |
|:----------------------------------------------|-----------:|------:|---------:|----------:|------:|----------:|-----------:|
| new ATS effect, pre-AI era (2021-22)          |      0.103 | 0.079 |   -0.051 |     0.257 | 0.189 | 41677.000 |     40.000 |
| DiD interaction: extra new-ATS effect, AI era |      0.145 | 0.091 |   -0.033 |     0.323 | 0.111 | 41677.000 |     40.000 |
| post-era gap, new vs legacy (sum of the two)  |      0.248 | 0.090 |    0.071 |     0.425 | 0.006 | 41677.000 |     40.000 |

*Sample:* n=41677, 40 center clusters.
*Notes:* Outcome: reopen_rate_6mo_pct (percentage points). Same FE/controls/cluster as E01b.
*Source:* analysis/02_retention_trend.py
