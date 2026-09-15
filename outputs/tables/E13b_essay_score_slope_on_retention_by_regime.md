### E13b. Essay-score slope on retention, by regime and by whether the applicant spent under 15 minutes in the situational section

|    | regime      |   fast_lt_15min |   estimate |    se |   ci_low |   ci_high |   n_cell |
|---:|:------------|----------------:|-----------:|------:|---------:|----------:|---------:|
|  0 | legacy_pre  |               0 |      0.008 | 0.001 |    0.006 |     0.009 |    11699 |
|  1 | legacy_pre  |               1 |      0.008 | 0.003 |    0.002 |     0.014 |     1341 |
|  2 | legacy_post |               0 |      0.004 | 0.002 |    0.000 |     0.008 |     5270 |
|  3 | legacy_post |               1 |     -0.001 | 0.004 |   -0.009 |     0.007 |     1056 |
|  4 | new_pre     |               0 |      0.009 | 0.002 |    0.006 |     0.012 |     5353 |
|  5 | new_pre     |               1 |      0.012 | 0.003 |    0.006 |     0.018 |      567 |
|  6 | new_post    |               0 |      0.004 | 0.001 |    0.002 |     0.006 |     9876 |
|  7 | new_post    |               1 |     -0.016 | 0.002 |   -0.021 |    -0.012 |     6515 |

*Sample:* 41,677 hires with an observed outcome.
*Notes:* Outcome: retained_6mo. essay x cell x fast15 slopes with cell x fast15 main effects, center + start-month FE, cluster center. fast_lt_15min=1 means essay_section_minutes < 15.
*Source:* analysis/06_essay_validity.py
