### E10f. Recruiter minutes per application vs applications per opening

|                  |   estimate |    se |   ci_low |   ci_high |     p |        n |   clusters |
|:-----------------|-----------:|------:|---------:|----------:|------:|---------:|-----------:|
| Intercept        |      9.730 | 0.072 |    9.589 |     9.872 | 0.000 | 2400.000 |     40.000 |
| apps_per_opening |     -0.023 | 0.000 |   -0.024 |    -0.022 | 0.000 | 2400.000 |     40.000 |

*Sample:* n=2400 center-months, 40 center clusters.
*Notes:* Outcome: recruiter_minutes_per_application. FE: center, month. Cluster: center. A negative coefficient means each extra applicant per opening buys less review time per application: recruiters spread a fixed capacity over a growing queue.
*Source:* analysis/04_recruiter_capacity.py
