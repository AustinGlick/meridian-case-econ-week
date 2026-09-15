### E12d. Essay-score slope on reopen rate, by regime (flex placements -- NOT selected on the essay by Meridian)

|    | regime      |   estimate |    se |   ci_low |   ci_high |   n_cell |   weighted_estimate |   weighted_se |
|---:|:------------|-----------:|------:|---------:|----------:|---------:|--------------------:|--------------:|
|  0 | legacy_pre  |     -0.179 | 0.010 |   -0.199 |    -0.160 |     9079 |              -0.177 |         0.010 |
|  1 | legacy_post |     -0.122 | 0.012 |   -0.146 |    -0.098 |     5541 |              -0.118 |         0.013 |
|  2 | new_pre     |     -0.207 | 0.019 |   -0.244 |    -0.169 |     2346 |              -0.212 |         0.021 |
|  3 | new_post    |     -0.069 | 0.007 |   -0.083 |    -0.056 |    11706 |              -0.069 |         0.007 |

*Sample:* n=28,672 flex placements, 40 center clusters.
*Notes:* Outcome: reopen_rate_pct. Controls: resume, license, prior years, referral, certification level. FE: center, placement_month. Cluster: center. A MORE NEGATIVE slope means the essay is more informative. Weighted columns weight by claims_closed.
*Source:* analysis/06_essay_validity.py
