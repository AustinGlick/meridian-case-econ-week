### E10c. Drivers of days-to-fill

|                                   |   estimate |    se |   ci_low |   ci_high |     p |        n |   clusters |
|:----------------------------------|-----------:|------:|---------:|----------:|------:|---------:|-----------:|
| Intercept                         |     21.374 | 3.894 |   13.742 |    29.006 | 0.000 | 2400.000 |     40.000 |
| apps_per_opening                  |      0.028 | 0.011 |    0.006 |     0.049 | 0.011 | 2400.000 |     40.000 |
| recruiter_minutes_per_application |     -0.792 | 0.384 |   -1.544 |    -0.040 | 0.039 | 2400.000 |     40.000 |
| local_unemployment_rate           |      0.537 | 0.275 |   -0.002 |     1.075 | 0.051 | 2400.000 |     40.000 |

*Sample:* n=2400, 40 center clusters.
*Notes:* Outcome: days_to_fill. FE: center, month. Cluster: center.
*Source:* analysis/04_recruiter_capacity.py
