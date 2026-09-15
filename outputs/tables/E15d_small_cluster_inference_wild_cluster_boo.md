### E15d. Small-cluster inference: wild-cluster bootstrap on the headline essay-slope differences

| test                                                 |   difference |   cluster_se |   cluster_p |   wild_bootstrap_p_299 |         n |   clusters |
|:-----------------------------------------------------|-------------:|-------------:|------------:|-----------------------:|----------:|-----------:|
| hires: retention slope, new_post minus legacy_pre    |       -0.011 |        0.001 |       0.000 |                  0.000 | 41677.000 |     40.000 |
| hires: retention slope, legacy_post minus legacy_pre |       -0.004 |        0.002 |       0.063 |                  0.080 | 41677.000 |     40.000 |
| flex: reopen slope, new_post minus legacy_pre        |        0.110 |        0.013 |       0.000 |                  0.000 | 28672.000 |     40.000 |
| flex: reopen slope, legacy_post minus legacy_pre     |        0.057 |        0.016 |       0.000 |                  0.003 | 28672.000 |     40.000 |

*Sample:* Hires with an observed outcome (retention) and flex placements (reopen).
*Notes:* H0: the essay slope in the named cell equals the legacy pre-2023 slope. Rademacher wild cluster bootstrap, 299 draws, 40 center clusters, restricted model imposes H0. A p below 0.05 means the difference survives small-cluster inference.
*Source:* analysis/07_identification.py
