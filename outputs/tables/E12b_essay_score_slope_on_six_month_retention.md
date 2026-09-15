### E12b. Essay-score slope on six-month retention, by regime (hires)

|    | regime      |   estimate |    se |   ci_low |   ci_high |   n_cell |
|---:|:------------|-----------:|------:|---------:|----------:|---------:|
|  0 | legacy_pre  |      0.009 | 0.001 |    0.007 |     0.010 |    13040 |
|  1 | legacy_post |      0.005 | 0.002 |    0.001 |     0.008 |     6326 |
|  2 | new_pre     |      0.011 | 0.002 |    0.007 |     0.014 |     5920 |
|  3 | new_post    |     -0.003 | 0.001 |   -0.005 |    -0.000 |    16391 |

*Sample:* n=41,677, 40 center clusters.
*Notes:* Outcome: retained_6mo. Controls: resume, license, prior years, referral, interview score. FE: center, start_month. Cluster: center. Hires are selected on the essay, which attenuates every slope toward zero.
*Source:* analysis/06_essay_validity.py
