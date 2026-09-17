### E21. Re-ranking the new-ATS AI-era hires under a screen formula that drops the essay

| ranking                                                                        |         n |   retention |   reopen_pct |
|:-------------------------------------------------------------------------------|----------:|------------:|-------------:|
| all new-ATS AI-era hires                                                       | 16391.000 |       0.834 |        8.592 |
| top half within center under: current formula (essay weight 0.25)              |  8203.000 |       0.826 |        8.618 |
| top half within center under: essay weight set to 0                            |  8203.000 |       0.868 |        7.954 |
| top half within center under: essay to 0, license and referral weights doubled |  8203.000 |       0.869 |        7.897 |
| moved INTO the top half by: essay weight set to 0                              |  3699.000 |       0.864 |        8.072 |
| moved OUT of the top half by: essay weight set to 0                            |  3699.000 |       0.772 |        9.545 |
| moved INTO the top half by: essay to 0, license and referral weights doubled   |  3741.000 |       0.864 |        8.027 |
| moved OUT of the top half by: essay to 0, license and referral weights doubled |  3741.000 |       0.770 |        9.609 |

*Sample:* 16,391 new-ATS hires who applied 2023-01 or later with an observed six-month outcome; weights from recruiter_screen_score ~ inputs + center + month FE on 255,535 reviewed applications in the same cell (R-squared 0.82).
*Notes:* A lower-bound check, not a policy estimate: outcomes are unobserved for applicants the current formula rejected, so this only asks whether, among people already hired, the ones a reweighted formula would have ranked higher retain better than the ones it would have dropped. 'Top half' is within center. Doubling the license and referral weights is an illustrative reallocation, not a fitted one.
*Source:* analysis/05_screen_components.py
