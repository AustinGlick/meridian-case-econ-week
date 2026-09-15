### E13c. Essay score per minute spent in the section, by regime

| regime      |   estimate |    se |          n |
|:------------|-----------:|------:|-----------:|
| legacy_pre  |      0.054 | 0.001 | 135320.000 |
| legacy_post |      0.030 | 0.003 |  76215.000 |
| new_pre     |      0.034 | 0.001 |  62232.000 |
| new_post    |     -0.021 | 0.001 | 255535.000 |

*Sample:* All reviewed applications, by cell.
*Notes:* essay_rubric_score ~ essay_section_minutes + center FE + application-month FE, cluster center. Positive = longer effort earns a higher score.
*Source:* analysis/06_essay_validity.py
