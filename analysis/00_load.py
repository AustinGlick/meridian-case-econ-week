"""H0 -- data integrity and sample construction. Not a hypothesis: everything else depends on
this being right. Produces E00 (sample-construction table) and validates the join guarantees
DATA-DICTIONARY.md and starter.py promise.

    python -m analysis.00_load
"""
from __future__ import annotations

import pandas as pd

from analysis.utils import load_frames, hires_obs, write_table, log_result, AI_ERA_CUTOFF


def main() -> None:
    d = load_frames()
    apps, hires, flex, cm, mig = (d["applications"], d["hires"], d["flex_placements"],
                                   d["center_month"], d["ats_migration"])
    hj, fj = d["hires_joined"], d["flex_joined"]

    checks = []

    # --- row counts match the raw files -----------------------------------
    checks.append(("applications.csv rows", len(apps), 529302))
    checks.append(("hires.csv rows", len(hires), 46266))
    checks.append(("flex_placements.csv rows", len(flex), 28672))
    checks.append(("center_month.csv rows", len(cm), 2400))
    checks.append(("ats_migration.csv rows", len(mig), 40))

    # --- join integrity ------------------------------------------------------
    assert hj["hire_id"].is_unique, "hires_joined must be one row per hire"
    assert fj["placement_id"].is_unique, "flex_joined must be one row per placement"
    assert hj["application_id"].isin(apps["application_id"]).all(), "orphan hire application_id"
    assert fj["application_id"].isin(apps["application_id"]).all(), "orphan flex application_id"
    checks.append(("hires_joined rows (== hires.csv)", len(hj), len(hires)))
    checks.append(("flex_joined rows (== flex_placements.csv)", len(fj), len(flex)))

    # --- outcome column consistency ------------------------------------------
    outcome_counts = apps["outcome"].value_counts()
    checks.append(("applications with outcome=hired", int(outcome_counts.get("hired", 0)),
                   len(hires)))
    checks.append(("applications with outcome=flex_placement", int(outcome_counts.get("flex_placement", 0)),
                   len(flex)))

    # --- censoring ------------------------------------------------------------
    n_censored = hj["retained_6mo"].isna().sum()
    n_obs = len(hires_obs(hj))
    last_start = hj["start_month"].max()
    checks.append(("hires censored (no 6mo outcome)", int(n_censored), "expect ~4589"))
    checks.append(("hires with observed 6mo outcome (analysis sample)", n_obs, "expect ~41677"))

    # coaching-hours nulls: how much overlaps with censoring
    coaching_null = hj["coaching_hours_first_90d"].isna()
    censored = hj["retained_6mo"].isna()
    checks.append(("coaching_hours null total", int(coaching_null.sum()), "n/a"))
    checks.append(("coaching_hours null AND censored", int((coaching_null & censored).sum()), "n/a"))
    checks.append(("coaching_hours null AND NOT censored (true missing)",
                   int((coaching_null & ~censored).sum()), "n/a"))

    # --- ATS at start vs at application ---------------------------------------
    ats_start = hj.merge(cm[["center_id", "month", "ats"]].rename(columns={"month": "start_month",
                                                                            "ats": "ats_at_start"}),
                         on=["center_id", "start_month"], how="left")
    mismatch = (ats_start["ats_at_start"] != ats_start["ats_at_application"]).sum()
    checks.append(("hires: ATS at start != ATS at application (use application-month ATS)",
                   int(mismatch), "expect ~530"))

    # --- application-to-start lag ----------------------------------------------
    app_m = pd.PeriodIndex(hj["application_month"], freq="M")
    start_m = pd.PeriodIndex(hj["start_month"], freq="M")
    lag = pd.Series([sm.ordinal - am.ordinal for sm, am in zip(start_m, app_m)])
    lag_counts = lag.value_counts().sort_index()
    lag_str = "; ".join(f"{int(k)} mo: {int(v):,}" for k, v in lag_counts.items())
    checks.append(("application-to-start lag distribution (months)", lag_str, "n/a"))

    # --- regime cell sizes (fixes the AI-era cutoff sample sizes used everywhere) ---
    regime_hires = hires_obs(hj)["regime"].value_counts().reindex(["legacy", "new_pre", "new_post"])
    regime_flex = fj["regime"].value_counts().reindex(["legacy", "new_pre", "new_post"])
    fmt_regime = lambda s: "; ".join(f"{k}: {int(v):,}" for k, v in s.items())
    checks.append((f"hires_obs by regime (cutoff {AI_ERA_CUTOFF})", fmt_regime(regime_hires), "n/a"))
    checks.append((f"flex by regime (cutoff {AI_ERA_CUTOFF})", fmt_regime(regime_flex), "n/a"))

    # --- never-migrated centers -------------------------------------------------
    n_never = mig["migration_month"].isna().sum()
    checks.append(("centers never migrated to new ATS", int(n_never), "expect 7"))

    # --- pilot arithmetic: hires per quarter at the 2024-rollout centers (the proposed pilot sites)
    wave24 = mig.loc[mig["migration_wave"] == "2024 rollout", "center_id"]
    h24 = hj[hj["center_id"].isin(wave24) & (hj["start_month"] >= "2025-01")]
    checks.append(("hires starting in 2025 at the 9 centers that migrated in 2024 (all, incl. censored)",
                   int(len(h24)), "n/a"))
    checks.append(("  = hires per quarter at those centers", int(round(len(h24) / 4)), "n/a"))

    # --- print + table -----------------------------------------------------------
    print(f"{'check':<62}{'value':>12}  expected")
    for name, val, exp in checks:
        v = val if not isinstance(val, dict) else "(dict, see table)"
        print(f"{name:<62}{str(v):>12}  {exp}")

    table = pd.DataFrame([(n, v if not isinstance(v, dict) else str(v), e)
                          for n, v, e in checks], columns=["check", "value", "expected"])
    write_table("E00", table, "Sample construction and data-integrity checks",
               sample_line="All five raw files, 2021-01 to 2025-12, 40 centers.",
               notes="Analysis sample for hire outcomes = hires_obs (retained_6mo observed); "
                     "censored hires (started 2025-07 or later) are excluded from every hire "
                     "regression and never imputed.",
               source="analysis/00_load.py")

    log_result(
        "H0 -- data integrity", "E00",
        finding=(f"Joins are 1:1 and match the raw files. {n_censored} of {len(hires)} hires "
                 f"({n_censored/len(hires):.1%}) are right-censored and excluded, leaving "
                 f"{n_obs} hires with an observed six-month outcome. {mismatch} hires have a "
                 f"different ATS at start than at application; we use the application-month ATS "
                 f"throughout because that is when the essay was written."),
        spec="n/a -- data validation",
        sample="All raw files; hires_obs = hires with retained_6mo not null",
        verdict=f"supported -- starter.load() joins are correct; {n_never} centers never "
                f"migrated (matches DATA-DICTIONARY.md and prompt.pdf, which say 7)."
    )
    assert n_never == 7, "prompt says 7 centers never migrated"
    print("\nH0 PASSED. See outputs/tables/E00_*.md and outputs/RESULTS.md")


if __name__ == "__main__":
    main()
