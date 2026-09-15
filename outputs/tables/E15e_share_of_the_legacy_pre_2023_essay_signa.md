### E15e. Share of the legacy pre-2023 essay signal retained, by cell: hires sample vs flex sample

| regime      |   hires_share_of_legacy_pre_slope_retained |   flex_share_of_legacy_pre_slope_retained | range_retained   |
|:------------|-------------------------------------------:|------------------------------------------:|:-----------------|
| legacy_pre  |                                      1.000 |                                     1.000 | [100%, 100%]     |
| legacy_post |                                      0.547 |                                     0.681 | [55%, 68%]       |
| new_pre     |                                      1.232 |                                     1.153 | [115%, 123%]     |
| new_post    |                                      0.000 |                                     0.387 | [0%, 39%]        |

*Sample:* Slopes from E12b (hires) and E12d (flex). Negative hire slopes are clipped at 0% retained.
*Notes:* The two samples bracket the truth: hires are selected on the essay (attenuated, lower bound on retained signal); flex are not.
*Source:* analysis/07_identification.py
