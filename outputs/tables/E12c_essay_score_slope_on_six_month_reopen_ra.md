### E12c. Essay-score slope on six-month reopen rate, by regime (hires)

|    | regime      |   estimate |    se |   ci_low |   ci_high |   n_cell |
|---:|:------------|-----------:|------:|---------:|----------:|---------:|
|  0 | legacy_pre  |     -0.147 | 0.010 |   -0.167 |    -0.127 |    13040 |
|  1 | legacy_post |     -0.093 | 0.015 |   -0.123 |    -0.063 |     6326 |
|  2 | new_pre     |     -0.180 | 0.016 |   -0.212 |    -0.148 |     5920 |
|  3 | new_post    |      0.035 | 0.010 |    0.016 |     0.054 |    16391 |

*Sample:* n=41,677, 40 center clusters.
*Notes:* Outcome: reopen_rate_6mo_pct (percentage points). Negative = higher essay score predicts fewer reopens. Same FE/cluster as E12b.
*Source:* analysis/06_essay_validity.py
