### E00. Sample construction and data-integrity checks

|    | check                                                                               | value                                             | expected      |
|---:|:------------------------------------------------------------------------------------|:--------------------------------------------------|:--------------|
|  0 | applications.csv rows                                                               | 529302                                            | 529302        |
|  1 | hires.csv rows                                                                      | 46266                                             | 46266         |
|  2 | flex_placements.csv rows                                                            | 28672                                             | 28672         |
|  3 | center_month.csv rows                                                               | 2400                                              | 2400          |
|  4 | ats_migration.csv rows                                                              | 40                                                | 40            |
|  5 | hires_joined rows (== hires.csv)                                                    | 46266                                             | 46266         |
|  6 | flex_joined rows (== flex_placements.csv)                                           | 28672                                             | 28672         |
|  7 | applications with outcome=hired                                                     | 46266                                             | 46266         |
|  8 | applications with outcome=flex_placement                                            | 28672                                             | 28672         |
|  9 | hires censored (no 6mo outcome)                                                     | 4589                                              | expect ~4589  |
| 10 | hires with observed 6mo outcome (analysis sample)                                   | 41677                                             | expect ~41677 |
| 11 | coaching_hours null total                                                           | 4161                                              | n/a           |
| 12 | coaching_hours null AND censored                                                    | 571                                               | n/a           |
| 13 | coaching_hours null AND NOT censored (true missing)                                 | 3590                                              | n/a           |
| 14 | hires: ATS at start != ATS at application (use application-month ATS)               | 530                                               | expect ~530   |
| 15 | application-to-start lag distribution (months)                                      | 0 mo: 11,169; 1 mo: 31,475; 2 mo: 3,609; 3 mo: 13 | n/a           |
| 16 | hires_obs by regime (cutoff 2023-01)                                                | legacy: 19,366; new_pre: 5,920; new_post: 16,391  | n/a           |
| 17 | flex by regime (cutoff 2023-01)                                                     | legacy: 14,620; new_pre: 2,346; new_post: 11,706  | n/a           |
| 18 | centers never migrated to new ATS                                                   | 7                                                 | expect 7      |
| 19 | hires starting in 2025 at the 9 centers that migrated in 2024 (all, incl. censored) | 1698                                              | n/a           |
| 20 | = hires per quarter at those centers                                                | 424                                               | n/a           |

*Sample:* All five raw files, 2021-01 to 2025-12, 40 centers.
*Notes:* Analysis sample for hire outcomes = hires_obs (retained_6mo observed); censored hires (started 2025-07 or later) are excluded from every hire regression and never imputed.
*Source:* analysis/00_load.py
