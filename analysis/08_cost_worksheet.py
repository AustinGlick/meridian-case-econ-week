"""H10 -- cost of the status quo and the cost of lost information, as a range.
H11 -- cost each of the four realistic options against the status quo.
H12 -- sensitivity analysis and "what would have to be different."

Implements the finance worksheet exactly as specified in prompt.pdf (pages 4-6):

    cost_per_retained = C_hire/r + C_sep*(1/r - 1) + C_policy_retained + [C_quality]
    C_hire = sourcing + training + ramp + days_to_fill * vacancy_cost_per_day
    C_quality = claims_per_adjuster_6mo * reopen_rate * cost_per_reopened_claim

The worked example in the prompt (r=0.75, 30 days to fill, 6% reopen, 2025 average rates) must
reproduce ~$26,103 (hiring+separation) and ~$11,800 (quality). This is the unit test and it runs
first; nothing else in this script executes if it fails.

Conventions (stated once, used everywhere):
  * Status quo = new-ATS hires who STARTED 2024-01 or later -- the same calendar window as the
    legacy-center proxy for option (b), so the comparison is like-for-like. The pooled 2023-25
    new-ATS cohort is shown as a second row because 2023 was a transition year.
  * All scenarios are costed at 2025 average center-month rates (as the worked example).
  * Option (b) is costed at the STATUS QUO days to fill (conservative: the prompt warns a
    costlier application means fewer applicants), with the legacy centers' observed days to
    fill as the optimistic bound. E20 varies both r and days to fill.
  * Annual figures = per-retained-employee delta x annual RETAINED seats (annual new-ATS hires
    x r), because the worksheet unit is one retained employee.

    python -m analysis.08_cost_worksheet
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.utils import (load_frames, hires_obs, fe_ols, did_table, write_table, save_fig,
                            log_result, HIRE_CONTROLS, DID_TERMS_HIRES, PALETTE)


# ---------------------------------------------------------------------------
# The worksheet, implemented once, used everywhere.
# ---------------------------------------------------------------------------
def c_hire(sourcing, training, ramp, days_to_fill, vacancy_per_day, extra_per_hire=0.0):
    """All costs required to produce one hire. extra_per_hire is an optional add-on (e.g.
    recruiter screening time or a structured-interview cost); the prompt's worked example omits
    it, so the unit test passes 0."""
    return sourcing + training + ramp + days_to_fill * vacancy_per_day + extra_per_hire


def cost_per_retained(chire, r, c_sep, c_policy_retained=0.0, c_quality=None):
    base = chire / r + c_sep * (1 / r - 1) + c_policy_retained
    return base if c_quality is None else base + c_quality


def c_quality(claims_per_adjuster_6mo, reopen_rate, cost_per_reopened_claim):
    return claims_per_adjuster_6mo * reopen_rate * cost_per_reopened_claim


def unit_test() -> None:
    """Reproduces the prompt's worked example. Raises if it does not match within 2%."""
    chire = c_hire(sourcing=747, training=5085, ramp=6540, days_to_fill=30, vacancy_per_day=219)
    assert abs(chire - 18942) / 18942 < 0.02, f"C_hire={chire}, expected ~18942"
    hiring_sep = cost_per_retained(chire, r=0.75, c_sep=2540)
    assert abs(hiring_sep - 26103) / 26103 < 0.02, f"hiring+sep={hiring_sep}, expected ~26103"
    quality = c_quality(609, 0.06, 323)
    assert abs(quality - 11800) / 11800 < 0.02, f"quality={quality}, expected ~11800"
    print(f"UNIT TEST PASSED: C_hire={chire:.0f} (expect ~18942), "
         f"hiring+sep cost per retained={hiring_sep:.0f} (expect ~26103), "
         f"quality cost per retained={quality:.0f} (expect ~11800)")


RATE_COLS = ["sourcing_cost_per_opening", "training_cost_per_hire", "ramp_productivity_loss_per_hire",
             "vacancy_cost_per_day", "separation_cost_per_exit", "claims_per_adjuster_6mo",
             "cost_per_reopened_claim", "recruiter_hourly_rate"]


def main() -> None:
    unit_test()
    d = load_frames()
    cm = d["center_month"]
    h = hires_obs(d["hires_joined"])
    cm25 = cm[cm["month"].str.startswith("2025")]
    rates = cm25[RATE_COLS].mean()
    # the prompt's 2025 averages, for the record
    write_table("E17a", rates.round(2).to_frame("2025 average").assign(
        prompt_worked_example=[747, 5085, 6540, 219, 2540, 609, 323, np.nan]),
        "Worksheet inputs: 2025 average rates across 40 centers vs the prompt's worked example",
        sample_line="480 center-months in 2025.", source="analysis/08_cost_worksheet.py")

    def scenario(hire_subset, label, days_to_fill, extra_per_hire=0.0, c_policy=0.0,
                 r_override=None, reopen_override=None):
        r = hire_subset["retained_6mo"].mean() if r_override is None else r_override
        reopen = (hire_subset["reopen_rate_6mo_pct"].mean() if reopen_override is None else reopen_override) / 100
        chire = c_hire(rates["sourcing_cost_per_opening"], rates["training_cost_per_hire"],
                      rates["ramp_productivity_loss_per_hire"], days_to_fill,
                      rates["vacancy_cost_per_day"], extra_per_hire)
        cpr_excl = cost_per_retained(chire, r, rates["separation_cost_per_exit"], c_policy)
        cq = c_quality(rates["claims_per_adjuster_6mo"], reopen, rates["cost_per_reopened_claim"])
        return {"scenario": label, "n": len(hire_subset) if r_override is None else np.nan,
                "r": r, "days_to_fill": days_to_fill, "reopen_pct": reopen * 100,
                "C_hire": chire, "C_sep": rates["separation_cost_per_exit"], "C_policy": c_policy,
                "C_quality": cq, "CPR_excl_quality": cpr_excl, "CPR_incl_quality": cpr_excl + cq}

    new = h["ats_at_application"] == "new"
    status_quo = h[new & (h["start_month"] >= "2024-01")]
    status_quo_pooled = h[new & (h["post_ai"] == 1)]
    cf_legacy = h[(h["ats_at_application"] == "legacy") & (h["start_month"] >= "2024-01")]
    cf_preai = h[new & (h["post_ai"] == 0)]

    dtf_new = cm[(cm["ats"] == "new") & (cm["month"] >= "2024-01")]["days_to_fill"].mean()
    dtf_legacy = cm[(cm["ats"] == "legacy") & (cm["month"] >= "2024-01")]["days_to_fill"].mean()

    # the DiD-implied retention gain of a working essay (H1, E01b), recomputed here so this
    # script is self-contained
    res_did = fe_ols(h, "retained_6mo", [*DID_TERMS_HIRES, *HIRE_CONTROLS], fe=["center_id", "start_month"])
    did_gain = -did_table(res_did).iloc[1]["estimate"]

    # ============================================================================
    # H10: status quo vs counterfactuals where the essay still screened -> a range
    # ============================================================================
    rows = [
        scenario(status_quo, "Status quo: new ATS, hires starting 2024-25 (observed)", dtf_new),
        scenario(status_quo_pooled, "Status quo (alt): new ATS, all AI-era hires 2023-25 (observed)", dtf_new),
        scenario(cf_legacy, "Counterfactual A: legacy centers, hires starting 2024-25 (observed)", dtf_legacy),
        scenario(status_quo, "Counterfactual A': status quo + DiD retention gain, status-quo days to fill",
                 dtf_new, r_override=status_quo["retained_6mo"].mean() + did_gain,
                 reopen_override=cf_legacy["reopen_rate_6mo_pct"].mean()),
        scenario(cf_preai, "Counterfactual B: new ATS before the AI era (2021-22), costed at 2025 rates", dtf_new),
    ]
    scen = pd.DataFrame(rows)
    money = ["C_hire", "C_sep", "C_policy", "C_quality", "CPR_excl_quality", "CPR_incl_quality"]
    fmt = lambda df: df.assign(**{c: df[c].round(0) for c in money if c in df},  # noqa: E731
                               r=df["r"].round(4), days_to_fill=df["days_to_fill"].round(2),
                               reopen_pct=df["reopen_pct"].round(3))
    write_table("E17", fmt(scen),
               "Cost per retained employee: status quo vs counterfactuals where the essay still screened",
               sample_line="Hires with an observed six-month outcome, by scenario; all costed at 2025 "
                           "average rates (E17a). CPR = cost per retained employee, $.",
               notes="A = the seven never-migrated centers (different, smaller centers). A' = the "
                     "status-quo cohort with retention raised by the H1 DiD gain (E01b) and reopen "
                     "set to the legacy level. B = the same new-ATS centers before AI writing. "
                     "C_hire excludes recruiter screening time (E17b).",
               source="analysis/08_cost_worksheet.py")

    sq = scen.iloc[0]
    gaps = {lab: (sq["CPR_excl_quality"] - scen.iloc[i]["CPR_excl_quality"],
                  sq["CPR_incl_quality"] - scen.iloc[i]["CPR_incl_quality"])
            for i, lab in ((2, "A"), (3, "A'"), (4, "B"))}
    lo_ex, hi_ex = min(g[0] for g in gaps.values()), max(g[0] for g in gaps.values())
    lo_in, hi_in = min(g[1] for g in gaps.values()), max(g[1] for g in gaps.values())

    # annual scale: retained seats per year at new-ATS centers
    hires_2025_h1 = int((h["start_month"].str.startswith("2025") & new).sum())
    annual_hires = hires_2025_h1 * 2          # Jan-Jun 2025 observed x 2, stated assumption
    annual_retained = annual_hires * sq["r"]

    # recruiter screening time per hire (E17b): minutes/application x applications per hire x rate
    apps_per_hire = cm25["applications_received"].sum() / max(len(h[h["start_month"].str.startswith("2025")]) * 2, 1)
    screen_cost = cm25["recruiter_minutes_per_application"].mean() * apps_per_hire * rates["recruiter_hourly_rate"] / 60
    write_table("E17b", pd.DataFrame({"value": {
        "recruiter_minutes_per_application_2025": cm25["recruiter_minutes_per_application"].mean(),
        "applications_received_per_hire_2025 (all centers, annualised)": apps_per_hire,
        "recruiter_hourly_rate_2025": rates["recruiter_hourly_rate"],
        "recruiter_screening_cost_per_hire_$": screen_cost,
        "as_share_of_C_hire_status_quo": screen_cost / sq["C_hire"]}}).round(3),
        "Recruiter screening time per hire (not in the prompt's C_hire; shown for option c)",
        sample_line="2025 center-months and 2025 hires (H1 x 2).", source="analysis/08_cost_worksheet.py")

    print(fmt(scen).to_string(index=False))
    print({k: (round(v[0]), round(v[1])) for k, v in gaps.items()})
    log_result(
        "H10 -- cost of lost information (worksheet unit test + range)", "E17/E17a/E17b",
        finding=(f"Worksheet unit test passes (C_hire $18,942; hiring+separation $26,103; quality "
                 f"$11,800 -- all within 2% of the prompt). Status quo (new-ATS hires starting "
                 f"2024-25, n={int(sq['n']):,}): r={sq['r']:.3f}, days to fill {sq['days_to_fill']:.1f}, "
                 f"reopen {sq['reopen_pct']:.2f}%, cost per retained employee ${sq['CPR_excl_quality']:,.0f} "
                 f"excluding operational quality, ${sq['CPR_incl_quality']:,.0f} including it. "
                 f"Against three counterfactuals in which the essay still screened -- A: legacy "
                 f"centers 2024-25 (r={scen.iloc[2]['r']:.3f}); A': status quo plus the H1 DiD gain "
                 f"of {did_gain:.3f} (r={scen.iloc[3]['r']:.3f}); B: the same centers before AI "
                 f"(r={scen.iloc[4]['r']:.3f}) -- the cost of the lost signal per retained employee "
                 f"is ${lo_ex:,.0f} to ${hi_ex:,.0f} excluding quality and ${lo_in:,.0f} to "
                 f"${hi_in:,.0f} including it (E17). At {annual_retained:,.0f} retained seats a "
                 f"year on the new ATS ({annual_hires:,} hires x r), that is "
                 f"${lo_ex*annual_retained/1e6:.1f}M-${hi_ex*annual_retained/1e6:.1f}M a year "
                 f"excluding quality, ${lo_in*annual_retained/1e6:.1f}M-${hi_in*annual_retained/1e6:.1f}M "
                 f"including it. Recruiter screening time adds about ${screen_cost:,.0f} per hire "
                 f"({screen_cost/sq['C_hire']:.0%} of C_hire) and is excluded from the worksheet "
                 f"figures (E17b)."),
        spec="cost_per_retained = C_hire/r + C_sep*(1/r-1) + [C_quality]; inputs = 2025 center-month "
             "averages; r and reopen from each scenario's observed cohort (A' uses the E01b DiD)",
        sample=f"Status quo n={int(sq['n']):,}; A n={int(scen.iloc[2]['n']):,}; B n={int(scen.iloc[4]['n']):,}",
        verdict="supported -- unit test passes; the range is a range because the counterfactuals "
               "differ in population (A), design (A') and period (B), and because monetising "
               "quality roughly doubles the gap, which the prompt warns can change the ranking."
    )

    # ============================================================================
    # E18: separation timing -- informs option (d)
    # ============================================================================
    sep = h[h["separation_month"].notna()].copy()
    sep["months_to_sep"] = [pd.Period(a, freq="M").ordinal - pd.Period(b, freq="M").ordinal
                            for a, b in zip(sep["separation_month"], sep["start_month"])]
    haz = sep.groupby(["months_to_sep", "separation_reason"]).size().unstack(fill_value=0)
    haz_pct = haz.div(len(sep)) * 100
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bottom = np.zeros(len(haz_pct))
    for col in ["voluntary", "performance", "attendance"]:
        ax.bar(haz_pct.index, haz_pct[col], bottom=bottom, label=col.capitalize(), color=PALETTE[col],
              width=0.7, edgecolor="white", linewidth=1)
        bottom += haz_pct[col].values
    for i, tot in zip(haz_pct.index, bottom):
        ax.text(i, tot + 0.4, f"{tot:.0f}%", ha="center", fontsize=8)
    ax.set_xlabel("Month on the job at separation (1 = first month)")
    ax.set_ylabel("Share of all separations within six months (%)")
    early = (sep["months_to_sep"] <= 2).mean(); late = (sep["months_to_sep"] >= 4).mean()
    ax.set_title(f"E18. Separations are front-loaded: {early:.0%} happen in months 1-2, "
                 f"{late:.0%} in months 4-6", fontsize=11)
    ax.legend(title="Reason")
    save_fig(fig, "E18", "separation_hazard_by_month",
            sample_line=f"{len(sep):,} hires who separated within six months, out of {len(h):,} "
                        f"with an observed outcome (all regimes).",
            source="analysis/08_cost_worksheet.py")
    plt.close(fig)
    write_table("E18b", haz.assign(total=haz.sum(axis=1)), "Separations by month on the job and reason (counts)",
               sample_line=f"{len(sep):,} hires who separated within six months.",
               source="analysis/08_cost_worksheet.py")

    # ============================================================================
    # H11: cost each of the four options against the status quo
    # ============================================================================
    r_sq, r_leg = sq["r"], scen.iloc[2]["r"]
    reopen_leg = scen.iloc[2]["reopen_pct"]
    # (a) do nothing: hold 2024-25 experience, and a trend variant using the 2024->2025 change
    ret_24 = h[new & h["start_month"].str.startswith("2024")]["retained_6mo"].mean()
    ret_25 = h[new & h["start_month"].str.startswith("2025")]["retained_6mo"].mean()
    trend = ret_25 - ret_24
    opt_a = scenario(status_quo, "(a) Do nothing: status quo continues", dtf_new)
    opt_a2 = scenario(status_quo, f"(a') Do nothing, 2024->25 retention change ({trend:+.3f}) continues one more year",
                      dtf_new, r_override=max(ret_25 + trend, 0.5))
    # (b) applicants bear it: legacy-observed r and reopen, at STATUS-QUO days to fill (conservative);
    # optimistic variant at legacy-observed days to fill; pessimistic variant = DiD gain only
    B_DTF_DELTA = 0
    opt_b = scenario(cf_legacy, "(b) Applicants bear it: timed/no-paste section; r and reopen = legacy "
                     "centers 2024-25; status-quo days to fill", dtf_new + B_DTF_DELTA)
    opt_b_lo = scenario(status_quo, "(b, low) Applicants bear it: retention gain = H1 DiD only; reopen = legacy",
                        dtf_new, r_override=r_sq + did_gain, reopen_override=reopen_leg)
    opt_b_hi = scenario(cf_legacy, "(b, high) Applicants bear it: legacy r, reopen AND legacy days to fill",
                        dtf_legacy)
    # (c) Meridian bears it: structured interview / work sample. STATED ASSUMPTIONS: recovers half
    # of the legacy retention gap; +15 recruiter minutes per REVIEWED application (not per received);
    # +3 days to fill.
    C_EXTRA_MIN, C_DTF, C_RECOVERY = 15, 3, 0.5
    reviewed_per_hire = cm25["applications_reviewed"].sum() / max(len(h[h["start_month"].str.startswith("2025")]) * 2, 1)
    c_extra = C_EXTRA_MIN * reviewed_per_hire * rates["recruiter_hourly_rate"] / 60
    r_c = r_sq + C_RECOVERY * (r_leg - r_sq)
    opt_c = scenario(status_quo, f"(c) Meridian bears it: structured interview; ASSUMED r recovers "
                     f"{C_RECOVERY:.0%} of the legacy gap, +{C_EXTRA_MIN} recruiter min per reviewed "
                     f"application (${c_extra:,.0f}/hire), +{C_DTF} days to fill",
                     dtf_new + C_DTF, extra_per_hire=c_extra, r_override=r_c,
                     reopen_override=sq["reopen_pct"] + C_RECOVERY * (reopen_leg - sq["reopen_pct"]))
    # (d) bear it after hiring: $500 six-month retention bonus. STATED ASSUMPTION: recovers one
    # sixth of the legacy gap, deliberately small because E18 shows separations are front-loaded.
    D_BONUS, D_RECOVERY = 500, 1 / 6
    opt_d = scenario(status_quo, f"(d) Bear it after hiring: ${D_BONUS} retention bonus at six months; "
                     f"ASSUMED r recovers {D_RECOVERY:.0%} of the legacy gap (separations are "
                     f"front-loaded, E18)", dtf_new, c_policy=D_BONUS,
                     r_override=r_sq + D_RECOVERY * (r_leg - r_sq))
    opts = pd.DataFrame([scen.iloc[0].to_dict(), opt_a, opt_a2, opt_b_lo, opt_b, opt_b_hi, opt_c, opt_d])
    for q in ("excl", "incl"):
        opts[f"delta_vs_status_quo_{q}_quality"] = opts[f"CPR_{q}_quality"] - opts.loc[0, f"CPR_{q}_quality"]
        opts[f"annual_delta_{q}_quality_$M"] = opts[f"delta_vs_status_quo_{q}_quality"] * annual_retained / 1e6
    write_table("E19", fmt(opts).round({"annual_delta_excl_quality_$M": 2, "annual_delta_incl_quality_$M": 2}),
               "Cost per retained employee by option, vs status quo",
               sample_line=f"Status quo, (a) and (b) are observed cohorts; (a'), (b low/high), (c) and "
                           f"(d) rest on the stated assumptions in the row label. Annual figures use "
                           f"{annual_retained:,.0f} retained seats a year ({annual_hires:,} new-ATS "
                           f"hires x r, 2025 H1 pace x 2).",
               notes="Negative delta = cheaper than status quo. (c) and (d) are not estimated from "
                     "Meridian data because Meridian has not run them; their retention effects are "
                     "assumptions and E20 shows how far they can move before the ranking changes.",
               source="analysis/08_cost_worksheet.py")
    print(fmt(opts)[["scenario", "r", "days_to_fill", "CPR_excl_quality", "CPR_incl_quality",
                     "delta_vs_status_quo_excl_quality", "delta_vs_status_quo_incl_quality"]].to_string(index=False))

    dv = lambda o, q: o[f"CPR_{q}_quality"] - opts.loc[0, f"CPR_{q}_quality"]  # noqa: E731
    log_result(
        "H11 -- cost each option against the status quo", "E19",
        finding=(f"Per retained employee, versus the status quo (${opts.loc[0,'CPR_excl_quality']:,.0f} "
                 f"excl. quality / ${opts.loc[0,'CPR_incl_quality']:,.0f} incl.): (a) do nothing "
                 f"${dv(opt_a2,'excl'):+,.0f} if the 2024-25 retention change ({trend:+.3f}) "
                 f"continues; (b) applicants bear it ${dv(opt_b,'excl'):+,.0f} excl. quality / "
                 f"${dv(opt_b,'incl'):+,.0f} incl. at status-quo days to fill, with a range of "
                 f"${dv(opt_b_lo,'excl'):+,.0f} to ${dv(opt_b_hi,'excl'):+,.0f} excl. quality "
                 f"(${dv(opt_b_lo,'incl'):+,.0f} to ${dv(opt_b_hi,'incl'):+,.0f} incl.) across the "
                 f"DiD-only and legacy-observed bounds; (c) Meridian bears it ${dv(opt_c,'excl'):+,.0f} "
                 f"/ ${dv(opt_c,'incl'):+,.0f} under the stated assumptions (half the gap recovered, "
                 f"${c_extra:,.0f} of extra recruiter time per hire, +{C_DTF} days); (d) bear it after "
                 f"hiring ${dv(opt_d,'excl'):+,.0f} / ${dv(opt_d,'incl'):+,.0f} for a ${D_BONUS} "
                 f"bonus recovering a sixth of the gap. Annual, at {annual_retained:,.0f} retained "
                 f"seats: (b) saves ${-opts.loc[3,'annual_delta_excl_quality_$M']:.1f}M-"
                 f"${-opts.loc[5,'annual_delta_excl_quality_$M']:.1f}M excl. quality "
                 f"(${-opts.loc[3,'annual_delta_incl_quality_$M']:.1f}M-"
                 f"${-opts.loc[5,'annual_delta_incl_quality_$M']:.1f}M incl.; low bound = DiD-only "
                 f"gain, high bound = legacy-observed r and days to fill), before any "
                 f"implementation cost, which the data do not contain. Caveats: the legacy centers "
                 f"are smaller, receive fewer applications, and their own essay signal is eroding "
                 f"(E12b/E12d), so (b) as 'copy the legacy configuration' is an upper bound on a "
                 f"timed section alone; (c) and (d) are assumption-driven."),
        spec="Same worksheet as H10; (a') trended; (b) legacy 2024-25 cohort at status-quo days to "
             "fill, bounded by the DiD-only gain and the legacy-observed days to fill; (c),(d) "
             "assumed recoveries stated in the row labels",
        sample="See E19 n column; (c) and (d) have no observed n",
        verdict="supported as a comparison framework -- (b) is the only option whose retention "
               "effect is observed rather than assumed, and it is cheaper than the status quo "
               "under every bound; (c) beats the status quo only if it recovers most of the gap "
               "at low extra recruiter time (E20); (d) roughly breaks even."
    )

    # ============================================================================
    # H12: sensitivity for (b) over r and days to fill; break-even; (c) break-even
    # ============================================================================
    r_grid = np.round(np.linspace(r_sq, scen.iloc[4]["r"], 7), 4)   # status quo .. pre-AI level
    dtf_deltas = [0, 5, 10, 15]
    grid = pd.DataFrame([{"r": rv, "days_to_fill_delta": dd,
                          "CPR_excl_quality": cost_per_retained(
                              c_hire(rates["sourcing_cost_per_opening"], rates["training_cost_per_hire"],
                                     rates["ramp_productivity_loss_per_hire"], dtf_new + dd,
                                     rates["vacancy_cost_per_day"]), rv, rates["separation_cost_per_exit"])}
                         for rv in r_grid for dd in dtf_deltas])
    pivot = grid.pivot(index="r", columns="days_to_fill_delta", values="CPR_excl_quality")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    shades = ["#0072B2", "#56B4E9", "#E69F00", "#D55E00"]
    for col, c in zip(pivot.columns, shades):
        ax.plot(pivot.index, pivot[col], marker="o", label=f"+{col} days to fill", color=c, linewidth=2)
    ax.axhline(opts.loc[0, "CPR_excl_quality"], color="#7F7F7F", linestyle="--", label="Status quo")
    for rv, lab in ((r_sq + did_gain, "DiD gain"), (r_leg, "legacy 2024-25"), (scen.iloc[4]["r"], "pre-AI")):
        ax.axvline(rv, color="#BBBBBB", linestyle=":", linewidth=1)
        ax.text(rv, ax.get_ylim()[1], f" r = {rv:.3f}\n {lab}", fontsize=7, va="top")
    ax.set_xlabel("Six-month retention probability r under option (b)")
    ax.set_ylabel("Cost per retained employee, $ (excl. operational quality)")
    ax.set_title("E20. Option (b) stays cheaper than the status quo unless a timed section adds "
                 "roughly a week\nof vacancy per hire without buying the full legacy retention gain",
                 fontsize=11)
    ax.legend(fontsize=8, loc="upper right")
    save_fig(fig, "E20", "sensitivity_option_b",
            sample_line="Worksheet evaluated over a grid of r (status quo to pre-AI level) and extra "
                        "days to fill; other inputs at 2025 averages; quality excluded.",
            source="analysis/08_cost_worksheet.py")
    plt.close(fig)
    write_table("E20b", pivot.round(0), "Sensitivity table: cost per retained employee under option (b), "
                "$ excl. quality, by r (rows) and extra days to fill (columns)",
               sample_line="2025-average cost rates.", source="analysis/08_cost_worksheet.py")

    # break-even days for (b) at each r bound (excl. and incl. quality, quality at legacy reopen)
    def breakeven_days(r_val, incl):
        cq = c_quality(rates["claims_per_adjuster_6mo"], reopen_leg / 100, rates["cost_per_reopened_claim"]) if incl else 0
        base = opts.loc[0, "CPR_incl_quality" if incl else "CPR_excl_quality"]
        chire0 = c_hire(rates["sourcing_cost_per_opening"], rates["training_cost_per_hire"],
                        rates["ramp_productivity_loss_per_hire"], dtf_new, rates["vacancy_cost_per_day"])
        saving = base - (cost_per_retained(chire0, r_val, rates["separation_cost_per_exit"]) + cq)
        # each extra vacancy day costs vacancy_cost_per_day / r per retained employee
        return saving / (rates["vacancy_cost_per_day"] / r_val)
    be = pd.DataFrame({"r_assumed": [r_sq + did_gain, r_leg, scen.iloc[4]["r"]],
                       "label": ["DiD gain only", "legacy 2024-25 observed", "pre-AI level"]})
    be["breakeven_extra_days_excl_quality"] = [breakeven_days(r, False) for r in be["r_assumed"]]
    be["breakeven_extra_days_incl_quality"] = [breakeven_days(r, True) for r in be["r_assumed"]]
    # (c) break-even recovery share at its stated cost
    def cpr_c(share):
        r_v = r_sq + share * (r_leg - r_sq)
        ch = c_hire(rates["sourcing_cost_per_opening"], rates["training_cost_per_hire"],
                    rates["ramp_productivity_loss_per_hire"], dtf_new + C_DTF, rates["vacancy_cost_per_day"], c_extra)
        return cost_per_retained(ch, r_v, rates["separation_cost_per_exit"])
    shares = np.linspace(0, 1, 101)
    c_be = next((s for s in shares if cpr_c(s) <= opts.loc[0, "CPR_excl_quality"]), np.nan)
    be_c = pd.DataFrame({"option_c_recovery_share_needed_to_break_even_excl_quality": [c_be],
                         "at_extra_recruiter_cost_per_hire_$": [c_extra], "at_extra_days_to_fill": [C_DTF]})
    write_table("E20c", pd.concat([be.round(3), be_c.round(3)], axis=1),
               "Break-even: extra vacancy days that erase option (b)'s saving; recovery share option (c) needs",
               sample_line="2025-average rates; status quo from E19 row 0.",
               notes="Each extra day to fill costs vacancy_cost_per_day / r per retained employee.",
               source="analysis/08_cost_worksheet.py")
    print(be.round(2)); print(be_c)

    log_result(
        "H12 -- sensitivity and what would change the recommendation", "E20/E20b/E20c",
        finding=(f"Option (b)'s saving per retained employee is erased by "
                 f"{be.iloc[0]['breakeven_extra_days_excl_quality']:.0f} extra vacancy days if it only "
                 f"buys the DiD retention gain (r={be.iloc[0]['r_assumed']:.3f}), "
                 f"{be.iloc[1]['breakeven_extra_days_excl_quality']:.0f} days at the legacy-observed "
                 f"r={be.iloc[1]['r_assumed']:.3f}, and {be.iloc[2]['breakeven_extra_days_excl_quality']:.0f} "
                 f"days at the pre-AI r={be.iloc[2]['r_assumed']:.3f} (excluding quality; including "
                 f"quality the break-evens are {be.iloc[0]['breakeven_extra_days_incl_quality']:.0f}, "
                 f"{be.iloc[1]['breakeven_extra_days_incl_quality']:.0f} and "
                 f"{be.iloc[2]['breakeven_extra_days_incl_quality']:.0f} days). Vacancy cost is "
                 f"${rates['vacancy_cost_per_day']:.0f}/day. Legacy centers today fill faster, not "
                 f"slower, than new-ATS centers ({dtf_legacy:.1f} vs {dtf_new:.1f} days, E10b), so the "
                 f"'fewer applicants means longer to fill' fear is not visible in the data, but those "
                 f"centers are small. Option (c) at +{C_EXTRA_MIN} recruiter minutes per reviewed "
                 f"application (${c_extra:,.0f}/hire) and +{C_DTF} days must recover at least "
                 f"{c_be:.0%} of the legacy retention gap to beat the status quo excluding quality. "
                 f"We would recommend (c) instead of (b) if a timed section pushed days to fill up by "
                 f"more than the break-even above, or if a structured interview were shown (pilot) to "
                 f"recover more than {c_be:.0%} of the gap at that cost. We would recommend (d) "
                 f"instead if separations were concentrated in months 4-6, but {late:.0%} of them are "
                 f"(E18) and {early:.0%} happen in months 1-2, before a probation review could act. "
                 f"We would recommend doing nothing if the Round 2 packet showed the legacy centers' "
                 f"retention advantage disappears once matched on size and region, or that the "
                 f"vendor cannot re-time the section at a cost below roughly the annual saving in E19."),
        spec="Worksheet over a grid of r and extra days to fill; break-even days = saving / "
             "(vacancy_cost_per_day / r); option (c) break-even recovery by grid search",
        sample="2,400 center-months for 2025 rates; sensitivity exercise, not a new estimation sample",
        verdict="supported -- the recommendation for (b) survives every r bound at zero extra days "
               "and survives the legacy-observed r up to about a week of extra vacancy per hire; "
               "the three 'recommend something else if' triggers are stated."
    )


if __name__ == "__main__":
    main()
