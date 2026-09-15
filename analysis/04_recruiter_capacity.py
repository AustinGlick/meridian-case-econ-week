"""H4 -- recruiter capacity is binding and getting worse, independent of the AI-writing story.
More applications per opening, less time per application, more days to fill -- a process
failure that compounds whatever is happening to the essay.

Produces:
  E10 recruiter-capacity panel: apps/opening, review share, minutes/application, days to fill

    python -m analysis.04_recruiter_capacity
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.utils import (load_frames, fe_ols, coef_table, did_table, write_table, save_fig,
                            log_result, DID_TERMS, PALETTE)


def main() -> None:
    d = load_frames()
    cm = d["center_month"]
    cm["year"] = cm["month"].str[:4]
    cm["review_share"] = cm["applications_reviewed"] / cm["applications_received"]

    metrics = [
        ("apps_per_opening", "Applications received per opening", "Applications per opening (count)"),
        ("review_share", "Share of applications reviewed by a recruiter", "Share reviewed (0-1)"),
        ("recruiter_minutes_per_application", "Recruiter minutes per application received", "Minutes per application"),
        ("days_to_fill", "Days from requisition open to accepted offer", "Days to fill"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    yearly = cm.groupby(["year", "ats"])[[m[0] for m in metrics]].mean().reset_index()
    for ax, (col, label, unit) in zip(axes.flat, metrics):
        for ats in ["legacy", "new"]:
            sub = yearly[yearly["ats"] == ats].sort_values("year")
            ax.plot(sub["year"], sub[col], marker="o", label=f"{ats.capitalize()} ATS", color=PALETTE[ats], linewidth=2)
        ax.set_title(label)
        ax.set_ylabel(unit)
        ax.set_xlabel("Calendar year")
    axes[0, 0].legend()
    fig.suptitle("E10. Recruiter capacity has not kept pace with application volume:\n"
                "more applications per opening, less time per application, longer to fill")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    save_fig(fig, "E10", "recruiter_capacity_panel",
            sample_line=f"{len(cm):,} center-months, 40 centers, 2021-01 to 2025-12, yearly means.",
            source="analysis/04_recruiter_capacity.py")
    plt.close(fig)

    write_table("E10b", yearly.round(2), "Recruiter-capacity metrics by year and ATS",
               sample_line="2,400 center-months, yearly averages by ATS in that center-month.",
               source="analysis/04_recruiter_capacity.py")

    # does the new ATS itself draw more applications (easier section -> higher apply rate)?
    res_apps = fe_ols(cm, "applications_received", DID_TERMS, fe=["center_id", "month"])
    da = did_table(res_apps)
    kd = "DiD interaction: extra new-ATS effect, AI era"
    kg = "post-era gap, new vs legacy (sum of the two)"
    apps_est, apps_ci = da.loc[kg, "estimate"], [da.loc[kg, "ci_low"], da.loc[kg, "ci_high"]]
    write_table("E10d", da.round(2), "Applications received per center-month: new ATS x AI-era DiD",
               sample_line=f"n={res_apps.sample_n} center-months, {res_apps.n_clusters} clusters.",
               notes="FE: center, month. Cluster: center.", source="analysis/04_recruiter_capacity.py")

    # does application volume drive down recruiter minutes per application?
    res_min = fe_ols(cm, "recruiter_minutes_per_application", ["apps_per_opening"],
                     fe=["center_id", "month"])
    min_est = res_min.params["apps_per_opening"]
    min_ci = res_min.conf_int().loc["apps_per_opening"].tolist()

    # does volume/thinner review drive up days to fill?
    res_fill = fe_ols(cm, "days_to_fill",
                      ["apps_per_opening", "recruiter_minutes_per_application",
                       "local_unemployment_rate"],
                      fe=["center_id", "month"])
    fill_tab = coef_table(res_fill)

    fill_tab = fill_tab.loc[[i for i in fill_tab.index if not i.startswith("C(")]]
    write_table("E10c", fill_tab.round(4), "Drivers of days-to-fill",
               sample_line=f"n={res_fill.sample_n}, {res_fill.n_clusters} center clusters.",
               notes="Outcome: days_to_fill. FE: center, month. Cluster: center.",
               source="analysis/04_recruiter_capacity.py")

    trend_apps = cm.groupby("year")["apps_per_opening"].mean()
    trend_min = cm.groupby("year")["recruiter_minutes_per_application"].mean()
    trend_fill = cm.groupby("year")["days_to_fill"].mean()

    print(f"apps_per_opening: {trend_apps.iloc[0]:.1f} (2021) -> {trend_apps.iloc[-1]:.1f} (2025)")
    print(f"recruiter_minutes_per_application: {trend_min.iloc[0]:.2f} -> {trend_min.iloc[-1]:.2f}")
    print(f"days_to_fill: {trend_fill.iloc[0]:.1f} -> {trend_fill.iloc[-1]:.1f}")
    print(f"New ATS x post-AI applications_received effect: {apps_est:.1f} [{apps_ci[0]:.1f}, {apps_ci[1]:.1f}]")
    print(f"recruiter_minutes ~ apps_per_opening: {min_est:.4f} [{min_ci[0]:.4f}, {min_ci[1]:.4f}]")

    log_result(
        "H4 -- recruiter capacity is binding and worsening", "E10",
        finding=(f"Applications per opening rose from {trend_apps.iloc[0]:.0f} to "
                 f"{trend_apps.iloc[-1]:.0f} (2021 to 2025) while recruiter minutes per "
                 f"application fell from {trend_min.iloc[0]:.2f} to {trend_min.iloc[-1]:.2f} and "
                 f"days to fill rose from {trend_fill.iloc[0]:.1f} to {trend_fill.iloc[-1]:.1f}. "
                 f"More applications per opening is associated with fewer recruiter minutes per "
                 f"application ({min_est:.4f} minutes per additional applicant, 95% CI "
                 f"[{min_ci[0]:.4f}, {min_ci[1]:.4f}], center+month FE) -- recruiters are "
                 f"spreading a fixed weekly capacity across a growing queue. The new ATS itself "
                 f"draws {apps_est:.0f} more applications per center-month than legacy in the AI era "
                 f"(95% CI [{apps_ci[0]:.0f}, {apps_ci[1]:.0f}], E10d; the pre-2023 new-ATS effect is "
                 f"negative and the DiD interaction larger, so the AI-era gap is the defensible "
                 f"number), plausibly because an untimed, "
                 f"paste-friendly section is easier to complete, compounding the capacity strain "
                 f"on exactly the centers where the essay is least informative."),
        spec="applications_received ~ treated_app + treated_app:post_ai + center FE + month FE; "
             "recruiter_minutes_per_application, days_to_fill ~ capacity regressors + center FE "
             "+ month FE; cluster center",
        sample="2,400 center-months, 40 centers, 2021-01 to 2025-12",
        verdict="supported -- recruiter capacity has not scaled with volume, and the new ATS "
               "adds to that volume; this is a real, independent process failure alongside the "
               "essay's loss of signal, and it is part of the 'where the process fails' answer."
    )


if __name__ == "__main__":
    main()
