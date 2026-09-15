### E11c. How much weight recruiters place on the essay score, by regime

|    | regime      |   essay_weight_in_screen_score |    se |   ci_low |   ci_high |      n |   r_squared |
|---:|:------------|-------------------------------:|------:|---------:|----------:|-------:|------------:|
|  0 | legacy_pre  |                          0.250 | 0.000 |    0.250 |     0.251 | 135320 |       0.862 |
|  1 | legacy_post |                          0.250 | 0.001 |    0.249 |     0.251 |  76215 |       0.848 |
|  2 | new_pre     |                          0.250 | 0.000 |    0.249 |     0.250 |  62232 |       0.861 |
|  3 | new_post    |                          0.249 | 0.000 |    0.249 |     0.250 | 255535 |       0.821 |

*Sample:* All reviewed applications, split by regime.
*Notes:* Outcome: recruiter_screen_score. FE: center, application_month. Cluster: center. An R-squared near 1 means the screen score is a fixed formula of its inputs, not a judgment.
*Source:* analysis/05_screen_components.py
