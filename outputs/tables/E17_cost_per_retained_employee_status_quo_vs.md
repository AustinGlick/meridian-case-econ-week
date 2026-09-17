### E17. Cost per retained employee: status quo vs counterfactuals where the essay still screened

|    | scenario                                                                    |         n |     r |   days_to_fill |   reopen_pct |    C_hire |   C_quality |   CPR_excl_quality |   CPR_incl_quality |
|---:|:----------------------------------------------------------------------------|----------:|------:|---------------:|-------------:|----------:|------------:|-------------------:|-------------------:|
|  0 | Status quo: new ATS, hires starting 2024-25 (observed)                      | 11440.000 | 0.820 |         28.930 |        8.918 | 18699.000 |   17531.000 |          23377.000 |          40908.000 |
|  1 | Status quo (alt): new ATS, all AI-era hires 2023-25 (observed)              | 16391.000 | 0.834 |         28.930 |        8.592 | 18699.000 |   16888.000 |          22916.000 |          39804.000 |
|  2 | Counterfactual A: legacy centers, hires starting 2024-25 (observed)         |  2487.000 | 0.857 |         27.260 |        7.985 | 18334.000 |   15695.000 |          21821.000 |          37516.000 |
|  3 | Counterfactual A': status quo + DiD retention gain, status-quo days to fill |   nan     | 0.843 |         28.930 |        7.985 | 18699.000 |   15695.000 |          22665.000 |          38360.000 |
|  4 | Counterfactual B: new ATS before the AI era (2021-22), costed at 2025 rates |  5920.000 | 0.882 |         28.930 |        7.645 | 18699.000 |   15027.000 |          21547.000 |          36574.000 |

*Sample:* Hires with an observed six-month outcome, by scenario; all costed at 2025 average rates (E17a). CPR = cost per retained employee, $.
*Notes:* C_sep = $2,540 per exit and C_policy = $0 in every row (not printed). A = the seven never-migrated centers (different, smaller centers). A' = the status-quo cohort with retention raised by the H1 DiD gain (E01b) and reopen set to the legacy level. B = the same new-ATS centers before AI writing. C_hire excludes recruiter screening time (E17b).
*Source:* analysis/08_cost_worksheet.py
