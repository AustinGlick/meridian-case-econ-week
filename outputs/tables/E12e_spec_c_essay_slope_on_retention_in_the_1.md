### E12e. Spec C: essay slope on retention in the 12 months before vs after a center's own ATS migration (2023/24 waves) vs never-migrated centers over the same calendar window

|    | group                                        | window           |   estimate |    se |   ci_low |   ci_high |    n |
|---:|:---------------------------------------------|:-----------------|-----------:|------:|---------:|----------:|-----:|
|  0 | 2023/24-wave centers, own migration month    | 12 months before |      0.006 | 0.002 |    0.002 |     0.010 | 8327 |
|  1 | 2023/24-wave centers, own migration month    | 12 months after  |     -0.002 | 0.002 |   -0.006 |     0.003 | 8327 |
|  2 | never-migrated centers, pseudo-event 2023-09 | 12 months before |      0.007 | 0.003 |    0.002 |     0.012 | 2359 |
|  3 | never-migrated centers, pseudo-event 2023-09 | 12 months after  |     -0.003 | 0.002 |   -0.007 |     0.001 | 2359 |

*Sample:* 8,327 hires at 2023/2024-wave centers; 2,359 hires at never-migrated centers.
*Notes:* Same controls/FE/cluster as E12b. The never-migrated slope also falls over this window (calendar 2022-09 to 2024-08), so the migration itself is not the whole story: the AI era degrades the timed section too, more slowly.
*Source:* analysis/06_essay_validity.py
