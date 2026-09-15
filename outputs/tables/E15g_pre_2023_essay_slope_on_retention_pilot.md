### E15g. Pre-2023 essay slope on retention: pilot centers vs never-migrated centers

| centers                            |   essay_slope_on_retention |   se_cluster_center |   ci_low |   ci_high |   n_hires |   clusters |
|:-----------------------------------|---------------------------:|--------------------:|---------:|----------:|----------:|-----------:|
| 2021 vendor pilot (migrated 2021)  |                      0.010 |               0.001 |    0.007 |     0.012 |  8012.000 |     12.000 |
| Never migrated (legacy throughout) |                      0.008 |               0.002 |    0.005 |     0.012 |  2393.000 |      7.000 |

*Sample:* Hires applying before 2023-01 with an observed six-month outcome: 8,012 at pilot centers, 2,393 at never-migrated centers.
*Notes:* retained_6mo ~ essay_rubric_score + controls, center FE + start-month FE, SEs clustered by center. If migration had selected centers where the essay was more or less valid, these slopes would differ.
*Source:* analysis/07_identification.py
