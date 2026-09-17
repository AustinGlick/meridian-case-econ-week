### E12f. Essay slope in the post-cutoff cells under alternative AI-era cutoffs

| cutoff   | cell        |   hires_retention_slope |   hires_ci_low |   hires_ci_high |   hires_n |   flex_reopen_slope |   flex_ci_low |   flex_ci_high |   flex_n |
|:---------|:------------|------------------------:|---------------:|----------------:|----------:|--------------------:|--------------:|---------------:|---------:|
| 2022-07  | legacy_post |                   0.006 |          0.004 |           0.009 |      9031 |              -0.138 |        -0.155 |         -0.121 |     7632 |
| 2022-07  | new_post    |                  -0.001 |         -0.004 |           0.001 |     18435 |              -0.076 |        -0.090 |         -0.062 |    12481 |
| 2023-01  | legacy_post |                   0.005 |          0.001 |           0.008 |      6326 |              -0.122 |        -0.146 |         -0.098 |     5541 |
| 2023-01  | new_post    |                  -0.003 |         -0.005 |          -0.000 |     16391 |              -0.070 |        -0.083 |         -0.056 |    11706 |
| 2023-07  | legacy_post |                   0.003 |         -0.002 |           0.007 |      4003 |              -0.119 |        -0.151 |         -0.086 |     3802 |
| 2023-07  | new_post    |                  -0.005 |         -0.008 |          -0.003 |     13985 |              -0.062 |        -0.076 |         -0.047 |    10580 |

*Sample:* Hires with an observed outcome (retention slope) and flex placements (reopen slope); the four-cell regime is rebuilt at each cutoff month.
*Notes:* Same specification as E12b (hires) and E12d (flex). The configured cutoff is 2023-01; E06b's grid search peaks at 2023-12 because the score rise is a ramp. If the new_post slope stays near zero on hires and well above the legacy_post slope on flex at every cutoff, the conclusion does not depend on the month chosen.
*Source:* analysis/06_essay_validity.py
