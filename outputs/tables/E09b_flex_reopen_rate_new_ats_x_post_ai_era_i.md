### E09b. Flex reopen rate: new ATS x post-AI-era interaction

| term                                          |   estimate |    se |   ci_low |   ci_high |     p |         n |   clusters |
|:----------------------------------------------|-----------:|------:|---------:|----------:|------:|----------:|-----------:|
| new ATS effect, pre-AI era (2021-22)          |      0.006 | 0.125 |   -0.239 |     0.252 | 0.961 | 28672.000 |     40.000 |
| DiD interaction: extra new-ATS effect, AI era |     -0.075 | 0.136 |   -0.342 |     0.192 | 0.581 | 28672.000 |     40.000 |
| post-era gap, new vs legacy (sum of the two)  |     -0.069 | 0.085 |   -0.236 |     0.098 | 0.418 | 28672.000 |     40.000 |

*Sample:* n=28672, 40 center clusters.
*Notes:* Outcome: reopen_rate_pct. Controls: certification_level FE. FE: center, placement_month. Cluster: center.
*Source:* analysis/03_pool_quality.py
