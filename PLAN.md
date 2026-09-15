# Meridian Casualty case competition — analysis plan

## Context

Econ Week 2026 case ("Hiring Is Broken — Can You Fix It?"). Round 1 deliverable is a 4-page PDF
narrative plus an unlimited appendix of exhibits. Three required answers:

- **(a)** What the hiring process gets right and where it fails (a judgment, not a list).
- **(b)** Whether the situational section (essay) still works as a screen, and *how you know*
  (which comparison, on whom, what must be true for it to mean what we say).
- **(c)** One recommendation from {do nothing, applicants bear it, Meridian bears it, bear it after
  hiring}, costed with the finance worksheet against the status quo, plus "what would have to be
  different for me to recommend something else."

Judging rules that shape everything below: lead with the recommendation; **report defended ranges,
not point estimates**; name the hole in the analysis; every number in the narrative lives in an
appendix exhibit; every graph has labelled axes, units, and sample statement; regression and
causal-inference tools are sufficient.

This plan is written so a lower-capability model can execute it step by step. Each hypothesis
lists: the claim, the exact comparison, sample, specification, the exhibit it produces, and what
result would falsify it. `DATA-DICTIONARY.md` and `starter.py` were added by a prior model and are
NOT competition materials, but `starter.py`'s `load()` is correct and should be reused.

## What the data already show (from a read-only descriptive pass — verify in Step 0)

| fact | number |
|---|---|
| reviewed applications / hires / flex placements | 529,302 / 46,266 / 28,672 |
| hires with no 6-month outcome (censored, started 2025-07+) | 4,589 |
| hires with blank coaching hours | 4,161 (check overlap with censored) |
| hires whose ATS at start ≠ ATS at application | 530 (use ATS at application) |
| start month − application month | 0 mo: 11,169 · 1 mo: 31,475 · 2 mo: 3,609 · 3 mo: 13 |
| mean essay score, legacy ATS, 2021 → 2025 | 17.2 → 18.1 |
| mean essay score, new ATS, 2021 → 2025 | 18.0 → 20.7 (jump begins 2023, large in 2024–25) |
| median essay minutes, new ATS, 2021 → 2025 | 27.0 → 15.6 (legacy: 26.9 → 23.4) |
| share of applications with essay ≥ 24 | legacy 9.2 %, new 21 % |
| share with essay minutes < 10 | legacy 7 %, new 18.9 % |
| 6-mo retention, hires applying under legacy, by start year 21→25 | .879 .880 .882 .860 .847 |
| 6-mo retention, hires applying under new, by start year 21→25 | .873 .884 .871 .819 .820 |
| corr(essay, retained) among hires | legacy +0.054, new −0.034 |
| corr(essay, reopen rate) among flex placements | legacy −0.219, new −0.116 |
| corr(essay minutes, retained) among hires | legacy +0.049, new +0.103 |
| apps per opening, 2021 → 2025 | 150 → 217 |
| recruiter minutes per application, 2021 → 2025 | 6.22 → 2.95 |
| days to fill, 2021 → 2025 | 22.4 → 29.6 |
| separations by reason 2023 → 2024 | performance 318→537, attendance 289→386, voluntary 560→656 |

Emerging story (to be tested, not assumed): the new ATS alone did not break the essay (pilot
centers ran it 2021–22 with no damage). The essay broke when untimed/paste-enabled met widely
available AI writing (2023 onward), inflating scores and destroying their predictive content.
Recruiters, now with half the minutes per application, still screen on the inflated score, so
Meridian hires more people who look good on paper and fail on performance/attendance. The 7
never-migrated (legacy) centers are a live counterfactual for "make applicants bear it."

## Environment setup (Step 0)

- Python 3.14 is installed but **pandas is not**. Install: `pip install pandas numpy statsmodels
  scipy matplotlib linearmodels`. If `linearmodels` fails on 3.14, use `statsmodels` OLS with
  dummies / `cov_type="cluster"` instead.
- Create repo layout:
  ```
  C:\Project\Econ Week\
    CLAUDE.md
    meridian-case-data\           (raw data, read-only; never modify)
    analysis\
      00_load.py                  wraps starter.load(); builds analysis frames; saves parquet/csv to build/
      01_descriptives.py          H0 + trend exhibits
      02_retention_trend.py       H1, H2
      03_pool_quality.py          H3
      04_recruiter_capacity.py    H4
      05_screen_components.py     H5
      06_essay_validity.py        H6, H7, H8  (core of deliverable b)
      07_identification.py        H9 (event study, placebos, bounds)
      08_cost_worksheet.py        H10–H12
      utils.py                    shared: sample filters, FE regression helper, table/figure writers
    build\                        intermediate frames (gitignored)
    outputs\
      exhibits\                   PNG figures, one per exhibit, named E01_..., E02_...
      tables\                     markdown + csv, one per exhibit
      RESULTS.md                  running log: every number, its exhibit id, its sample, its spec
    report\
      narrative_outline.md        4-page structure with exhibit references
  ```
- Every script: `from analysis.utils import load_frames` … writes to `outputs/` and appends to
  `RESULTS.md`. Scripts must be re-runnable from scratch: `python -m analysis.06_essay_validity`.

## Shared definitions (put in `analysis/utils.py`)

- `ats_app` = ATS in the center in the **application month** (starter's `ats_at_application`).
  Never use ATS at start month for essay questions.
- `era` = `post_ai` = 1 if application month ≥ 2023-01 (ChatGPT public Nov 2022). Step 1 must
  verify this break visually (monthly mean essay score, new vs legacy) and adjust if the data say
  the break is elsewhere; report the chosen date and the sensitivity to ±6 months.
- `treated_app` = `ats_app == "new"`. `treated × post_ai` is the key interaction.
- `hires_obs` = hires with `retained_6mo` not null (drop censored; NEVER impute).
- `fast_essay` = `essay_section_minutes < 10` (also try < 15; report both).
- Standard controls `X`: resume_score, has_adjuster_license, prior_claims_experience,
  prior_claims_years, referral, currently_employed. Add starting_wage, wage_index,
  local_unemployment_rate (at start month) for hire outcomes.
- Fixed effects: center FE always; month (calendar) FE; cluster SE by center (40 clusters →
  also report wild-cluster-bootstrap p or at least note the small-cluster caveat).
- Reopen outcomes: use rate, but also run count model or weight by claims_closed as robustness.
- Cost inputs: use **2025 center-month averages** (matches the worked example), and also the
  center-specific 2025 rates for a per-center range.

## Hypothesis tests, grouped by deliverable

### Deliverable (a): what the process gets right, where it fails

**H0 — Data integrity (not a hypothesis, but must come first).**
Reproduce the table above; confirm `starter.load()` merges 1:1; tabulate censoring by start month;
check coaching-hours nulls vs censoring; confirm every application_id in hires/flex exists in
applications; check `outcome` consistency (hired ↔ row in hires). Exhibit E00: sample-construction
table (rows in, rows dropped, why).

**H1 — Retention has declined, and the decline is concentrated in new-ATS centers after 2023.**
- Sample: hires_obs. Outcome: retained_6mo.
- Spec 1 (descriptive): retention by start-quarter × ats_app (line chart, E01).
- Spec 2 (DiD): `retained ~ treated_app × post_ai + X + center FE + start-month FE`, cluster center.
- Spec 3: same, outcome = reopen_rate_6mo_pct (E02).
- Spec 4: separation reason composition by year × ATS (E03). Multinomial or three LPMs:
  performance, attendance, voluntary. Prediction: performance/attendance share rises in
  treated×post; voluntary does not (rules out "labor market" story).
- Falsified if: decline is equal in legacy centers, or is explained by unemployment/wage controls.

**H2 — Whitfield's puzzle ("worst in our best-run centers") is the pilot-wave effect.**
- Pilot centers = large, strong IT = "best-run". They migrated first, so they are the longest
  exposed to the new ATS when AI arrived.
- Exhibit E04: retention by migration_wave × year (pilot / 2023 / 2024 / never).
- Exhibit E05: same with size_index tercile to show size alone does not explain it.
- Key check: pilot centers show **no** retention decline in 2021–22 despite being on the new ATS
  → ATS alone is not the mechanism; ATS × AI era is.
- Falsified if: pilot centers deteriorated immediately at migration in 2021–22.

**H3 — The applicant pool did not get better; the essay signal got inflated.**
- E06: monthly mean essay score, legacy vs new (this is the headline "break" chart; mark
  migration waves and 2023-01).
- E07: distribution of essay_section_minutes by ATS × era (histogram; show bimodality / mass <10).
- E08: objective applicant attributes over time by ATS (resume_score, license, prior years,
  referral, employed): should be flat → "stronger applicants" is an illusion of the rubric.
- E09: flex-placement reopen rates by placement year × ATS-at-application. Flex are the
  *unselected* applicants; if their quality is stable while essay scores rose, the pool didn't
  improve. (Control for certification_level, center FE.)
- Regression: `essay ~ treated_app × post_ai + X + center FE + month FE` → the inflation in points.
- Falsified if: resume/license/experience also improved in step, or flex quality improved.

**H4 — Recruiter capacity is binding and getting worse (process failure independent of AI).**
- Sample: center_month panel (2,400 rows).
- E10: apps_per_opening, applications_reviewed/received, recruiter_minutes_per_application,
  days_to_fill — yearly, legacy vs new.
- Spec: `days_to_fill ~ apps_per_opening + recruiter_minutes_per_application + local_unemployment
  + center FE + month FE`. And `recruiter_minutes ~ apps_per_opening + FE`.
- Question to answer: are recruiters reviewing a smaller, less-carefully-read share? Does the
  review share fall more in new-ATS centers (which get more applications because the section is
  easier)? `applications_received ~ treated × post_ai + FE`.
- Falsified if: minutes per application and review share are stable.

**H5 — Which screen components still carry information (what the process gets right).**
- Sample: hires_obs. Outcome: retained_6mo and reopen rate.
- Spec: `outcome ~ essay + resume + license + prior_years + referral + employed + interview_score
  + coaching_hours + center FE + start-month FE`, run separately for (legacy, new×pre, new×post).
- Also the recruiter's own weighting: `recruiter_screen_score ~ essay + X` and
  `advanced_to_interview ~ essay + X` by regime. Do recruiters still lean on the essay as hard in
  the AI era? (If yes → the process has not adapted; that IS the failure.)
- Interview score: still predictive in all regimes? If yes → the interview is the working
  backstop and option (c)/(d) designs can build on it.
- Referral / license: expect stable predictive power (these are the "gets right" list).
- E11: coefficient plot, three regimes side by side, with 95 % CIs.

### Deliverable (b): does the situational section still work as a screen?

Be explicit in the write-up: **comparison** = predictive slope of essay score on 6-month outcomes;
**on whom** = (i) permanent hires, (ii) flex placements; **regimes** = legacy, new-pre-2023,
new-post-2023; **what must be true** = selection into the hire sample on the essay is the same
across regimes (it is not exactly — hence the bounds in H9), and flex placement is not selected on
the essay (partner places on certification, geography, availability — stated in the case).

**H6 — Core test: the essay predicts outcomes under legacy, and not under new ATS in the AI era.**
- Spec A (hires): `retained ~ essay × regime + X + interview + center FE + start-month FE`, cluster
  center. Report essay slope per regime with CI. Repeat for reopen_rate_6mo_pct.
- Spec B (flex): `reopen_rate_pct ~ essay × regime + X + certification_level FE + center FE +
  placement-month FE`. Weight by claims_closed as robustness. This is the cleaner test because
  Meridian did not select these people on the essay.
- Spec C (within-center before/after): restrict to 2023- and 2024-wave centers, compare essay
  slope in the 12 months before vs 12 months after migration; never-migrated centers as control
  over the same calendar windows. Migration during the AI era = the cleanest switch-on of the
  paste/untimed mechanism.
- Spec D (nonlinear): bin essay score (0–11, 12–17, 18–23, 24–30) × regime; plot retention by bin.
  Prediction: the top bin's advantage vanishes in new×post (E12, the key exhibit for (b)).
- Falsified if: essay slope in new×post is not statistically distinguishable from legacy, in both
  hires and flex samples.

**H7 — Mechanism: fast, high-scoring essays are the ones that don't predict.**
- Spec: `retained ~ essay × fast_essay × regime + X + FE` on hires; same on flex reopen.
- Prediction: among applicants with ≥ 15–20 minutes in the section, the essay still predicts even
  on the new ATS; among fast+high scorers it does not. E13: retention by (essay bin × minutes bin)
  under new×post.
- Also: `essay ~ minutes` slope by regime (positive under legacy, negative/flat under new×post).
- Why it matters: minutes-in-section is a free signal Meridian already collects; option (b)
  (re-time the section) and a cheap variant (flag fast essays) both follow from it.
- Falsified if: the essay is equally uninformative regardless of minutes under new×post.

**H8 — Placebo: other screen inputs did NOT lose predictive power at the same time.**
- Same Spec A/B, but the interaction of interest is `resume_score × regime`, `license × regime`,
  `prior_claims_years × regime`, `interview_score × regime`.
- Prediction: stable across regimes. If they also collapsed, the cause is not the essay/AI but
  something center-wide (labor market, management) — the recommendation would change.
- E14: placebo coefficient table.

**H9 — Identification threats, bounds, and the defended range.**
- Non-random migration: (i) event-study of retention around migration month by wave, with
  never-migrated as control, pre-trend test (E15); (ii) show pre-period (2021–22) essay slope is
  the same in pilot vs legacy centers (no selection into ATS on essay validity).
- Timing: essay-score break should track calendar 2023 in ALL new-ATS centers regardless of
  migration date (pilot centers migrated 2021 but break in 2023). Fit break date by grid search
  over 2022-07…2023-12 on the monthly new-ATS essay mean; report the best fit and the sensitivity.
- Selection on the essay into the hire sample: hires are truncated on the screen score, which
  attenuates the essay slope. Argue direction: attenuation is *larger* under legacy (fewer
  high-scorers hired? check the hired-share by essay bin per regime), so the hires-sample
  difference is a lower bound on signal loss. The flex sample gives the less-attenuated estimate.
  **Report the range: [hires-sample loss, flex-sample loss].**
- Alternative explanations to close: local_unemployment_rate and wage_index trends by ATS
  (E16); starting_wage relative to wage_index by regime; coaching_hours_first_90d by regime (did
  supervisors coach less?).
- Small-cluster caveat: 40 centers; report cluster-robust and wild-bootstrap p-values for the
  headline interaction.
- Name the hole explicitly: we cannot observe AI use; we cannot observe unreviewed applicants;
  migration was not random; 2025 cohorts are partly censored.

### Deliverable (c): recommendation and cost

**H10 — Cost of the status quo, and the cost of the lost information, as a range.**
- Implement the worksheet exactly:
  `CPR = C_hire / r + C_sep × (1/r − 1) + C_policy + [C_quality]`,
  `C_hire = sourcing_per_opening (÷ hires per opening if > 1, state it) + training + ramp +
  days_to_fill × vacancy_cost_per_day`, `C_quality = claims_per_adjuster_6mo × reopen × cost_per_reopened_claim`.
- Reproduce the worked example (r = .75, 30 days, 6 %) with 2025 averages → must give ≈ $26,103
  and ≈ $11,800. This is the unit test for the cost code.
- Status quo (2025 new-ATS centers): observed r, days_to_fill, reopen. Counterfactual "essay still
  worked": 2025 legacy-center r / reopen (option-(b) proxy) AND 2021–22 new-ATS r / reopen
  (pre-AI proxy). Two counterfactuals → a range.
- Multiply the per-retained-employee gap by annual retained hires (≈ 40 centers × 20/mo × 12 × r)
  for an annual dollar cost of lost information. Report with/without C_quality. E17.
- Should recruiter screening time be inside C_hire? Yes: `recruiter_minutes_per_application ×
  applications_received / hires × recruiter_hourly_rate / 60`. Compute it; it also tells you the
  cost of option (c).

**H11 — Cost each realistic option against the status quo (the recommendation).**
- (a) Do nothing: H10 status quo. Trend it forward one year (retention slope 2024→25).
- (b) Applicants bear it (re-time the section / disable paste; possibly proctor): the 7 legacy
  centers ARE this policy. Use their 2024–25 r, reopen, and days_to_fill as the counterfactual
  (matched on region/size where possible; note they are smaller centers). Estimate the applicant
  volume effect: `applications_received ~ treated × post_ai + FE` (fewer applicants under timed
  section?) and whether fewer applicants raise days_to_fill (`days_to_fill ~ apps_per_opening`).
  Implementation cost is not in the data: state an assumption (vendor config change, a one-time
  amount per center) and show the break-even.
- (c) Meridian bears it: more recruiter minutes per application / structured work sample. Test
  whether recruiter minutes buy anything: `retained ~ recruiter_minutes_per_application (at
  application month) × regime + X + FE`, and whether interview_score's slope suggests a
  heavier-weighted interview would recover the lost signal (simulate: re-rank applicants on
  interview + resume + license only, predicted retention of the top-k vs actual). Cost = extra
  recruiter hours × recruiter_hourly_rate per hire, plus days_to_fill change.
- (d) Bear it after hiring: use separation_month distribution (E18: hazard of separation by month
  on job, by reason, by regime). If performance/attendance exits cluster in months 4–6, a
  90-day probation decision cuts C_sep and the wasted training/ramp partially; if exits are
  already early, (d) buys little. Retention bonus = C_policy: back out the r improvement needed to
  break even for a given bonus size.
- Also test whether coaching hours predict retention (`retained ~ coaching_hours + X + FE`), since
  option (d) may be "coach more."
- E19: one table, four options, columns = r, days_to_fill, reopen, C_hire, C_sep term, C_policy,
  C_quality, CPR (with and without quality), Δ vs status quo, annual Δ at 2025 hiring volume.

**H12 — Sensitivity and "what would have to be true."**
- Tornado / sensitivity table (E20) for the recommended option over: r (range from H10),
  days_to_fill Δ (0, +5, +10, +15 days), reopen Δ, monetize quality yes/no, implementation cost.
- Break-even: how many extra vacancy days erase the retention gain? What r improvement does a
  $X retention bonus need?
- Write the three sentences: "I would recommend (c) instead if …", "(d) instead if …",
  "do nothing if …". Candidate triggers: legacy-center advantage disappears once matched on size
  and region; applicant volume under a timed section falls enough to push days_to_fill past the
  break-even; the placebo (H8) fails.
- Round 2 prep: list the packet contents that would flip the call (e.g., vendor says re-timing is
  impossible; legacy centers are being migrated anyway; a labor-market shock; reopen cost
  revised).

## Exhibit register (appendix)

E00 sample construction · E01 retention by quarter × ATS · E02 reopen by quarter × ATS ·
E03 separation reasons · E04 retention by wave × year · E05 by size tercile · E06 monthly essay
mean by ATS (headline) · E07 essay-minutes distributions · E08 objective attributes over time ·
E09 flex quality over time · E10 recruiter-capacity panel · E11 screen-component coefficients by
regime · E12 retention by essay bin × regime (headline for b) · E13 essay × minutes · E14 placebo
table · E15 migration event study · E16 labor-market controls · E17 cost of lost information ·
E18 separation hazard · E19 option comparison table · E20 sensitivity.
Every figure: title, axis labels with units, sample line under the plot ("Sample: 41,677 permanent
hires with an observed 6-month outcome, start months 2021-01 to 2025-06"), source note.

## Narrative outline (4 pages) — `report/narrative_outline.md`

1. **Recommendation up front** (½ page): the option, the cost range per retained employee and per
   year, the one-sentence reason, the hole.
2. **(a) The process** (1 page): what works (interview, license/referral signals, volume) and what
   fails (essay inflated, recruiters at half the minutes, screen still weights the essay). E01, E06,
   E10, E11.
3. **(b) The essay** (1½ pages): the comparison, on whom, what must be true; hires vs flex ranges;
   the mechanism (minutes); the placebo; the pilot-center timing argument; the hole. E12, E13, E14.
4. **(c) The decision** (1 page): the four options costed, sensitivity, what would change the
   call, Round-2 triggers. E19, E20.

## CLAUDE.md to write at `C:\Project\Econ Week\CLAUDE.md`

```markdown
# Meridian Casualty case — Econ Week 2026

## What this repo is
Team case-competition analysis. The case prompt is `prompt.pdf` (read it first, every session).
Raw data are in `meridian-case-data/` and are READ-ONLY. `DATA-DICTIONARY.md` and `starter.py`
in that folder were written by an earlier AI session, not by the competition; `starter.load()`
is correct and is the only way we load and join data.

## Deliverables (from the prompt)
(a) judgment on the hiring process, (b) whether the situational section still screens and HOW WE
KNOW, (c) one costed recommendation with what would change it. Four pages of narrative, unlimited
appendix. Lead with the recommendation. Report defended RANGES, never a lone point estimate.
Name the hole in the analysis. Every number in the text must point to an exhibit id.

## Layout
- `analysis/` numbered scripts, run in order; `analysis/utils.py` holds shared filters and helpers
- `build/` intermediate frames (disposable)
- `outputs/exhibits/` PNG figures `E##_name.png`; `outputs/tables/` `E##_name.md` + `.csv`
- `outputs/RESULTS.md` append-only log: every estimate, exhibit id, sample n, spec, SE type
- `report/narrative_outline.md` the 4-page structure
- Plan of record: the hypothesis list in this session's plan file (copied to `PLAN.md`)

## Non-negotiable analysis rules
- ATS regime = ATS in the APPLICATION month (`ats_at_application`), never start month.
- Regimes: `legacy`, `new & pre-2023`, `new & post-2023` (era cutoff verified in E06; if changed,
  change it in `utils.py` only).
- Drop right-censored hires (`retained_6mo` null). Never impute outcomes. State n after dropping.
- Flex placements are the not-selected-on-essay sample; say so whenever they are used.
- Center fixed effects always; calendar-month fixed effects; cluster SEs by center (40 clusters:
  also report wild-cluster bootstrap for headline interactions).
- Cost worksheet: implement exactly as the prompt; the worked example (r=.75, 30 days, 6 %,
  2025 averages → ≈ $26,103 and ≈ $11,800) is the unit test and must pass before any costing.
- Every figure: title, labelled axes with units, one-line sample statement, source note.
  Use the `dataviz` skill before writing any chart code.
- Never report a coefficient without n, SE type, and the exhibit id. Never round away a CI.
- Migration was NOT random (pilot = large centers with strong IT). Every causal claim must say
  what the identifying comparison is and what would have to be true.

## Workflow
- Python 3.14; `pip install pandas numpy statsmodels scipy matplotlib` first if missing.
- Run scripts as modules from the repo root: `python -m analysis.06_essay_validity`.
- Re-running any script must regenerate its exhibits from raw data (no hand-edited outputs).
- After each script: append findings to `outputs/RESULTS.md` (what, number, range, exhibit, spec).
- Do not start the narrative until H0–H12 are in RESULTS.md.
- Stay inside the prompt's scope: robustness serves the three answers; it is not a fourth answer.

## Writing rules for report text
- Plain English, no jargon without one-line definition; active voice; no hedging fog.
- Ranges with the reason they are ranges. "We could not determine X" is required, not optional.
- Spell-check. Every graph labelled. Every claim traceable to an exhibit.
```

## Using Claude skills on this project

Skills are on-demand instruction packs invoked with `/name` (or automatically when relevant).
CLAUDE.md is always-on context; skills are procedures loaded only when needed. For this project:

- **Built-in skills to use**
  - `/dataviz` — invoke before writing any figure code (E01–E20). It enforces labelled axes,
    consistent palette, light/dark legibility. Tell the model in CLAUDE.md to load it (done).
  - `/code-review` on `analysis/` before trusting numbers; `/simplify` after scripts stabilise.
  - `/init` is not needed — CLAUDE.md above replaces it.
- **Project skills to create** in `.claude/skills/<name>/SKILL.md` (frontmatter `name`,
  `description`, then instructions). Recommended:
  1. `regression-table` — how to run the standard FE/cluster spec via `utils.fe_ols()` and emit a
     markdown table with n, SE type, CI, exhibit id.
  2. `cost-worksheet` — the exact formula, the worked-example unit test, and the E19 table layout.
  3. `exhibit` — figure/table naming, sample line, source note, `RESULTS.md` logging format.
  4. `case-writing` — the 4-page rules: lead with recommendation, ranges, name the hole, exhibit refs.
  Invoke as `/regression-table`, etc. They are discovered automatically once the folder exists.
- **Skill vs CLAUDE.md rule of thumb**: put a rule in CLAUDE.md if it must hold in every session
  (data conventions, scope); put it in a skill if it is a multi-step procedure used at specific
  moments (making an exhibit, costing an option, drafting prose).
- **Handing off to a lower model**: give it `CLAUDE.md`, `PLAN.md`, and one hypothesis at a time
  ("Execute H6 per PLAN.md; write E12 and log to RESULTS.md"). Smaller models do best with one
  script per invocation and an explicit acceptance check (the falsification line in each H).

## Execution order for the lower model

**Status as of 2026-09-12:** packages installed; `CLAUDE.md`, `PLAN.md`, `analysis/utils.py`,
the folder scaffold, and the four project skills in `.claude/skills/` already exist.
`utils.py` has been smoke-tested (load_frames, add_regime, hires_obs, fe_ols, regime_slopes,
write_table). Start at writing `analysis/00_load.py`.

1. Step 0: write `00_load.py` (H0 sample-construction table E00) and the cost worked-example
   unit test inside `08_cost_worksheet.py`; both must pass before anything else.
2. H3 (E06) first — it fixes the era cutoff that everything else uses.
3. H1, H2, H4, H5 (deliverable a).
4. H6, H7, H8, H9 (deliverable b) — the core; spend the most time here.
5. H10, H11, H12 (deliverable c).
6. Narrative outline, then draft, then `/code-review` on scripts and a read-through of RESULTS.md
   to confirm every number in the draft has an exhibit.

## Verification

- `python -m analysis.00_load` prints the H0 table matching the numbers in this plan.
- Cost unit test reproduces $26,103 and ≈ $11,800.
- Each script re-runs cleanly from raw data and regenerates its exhibits.
- RESULTS.md contains, for every hypothesis, the estimate, CI, n, spec, exhibit id, and a one-line
  verdict (supported / not supported / mixed) against the falsification criterion.
- The narrative outline references only exhibit ids that exist in `outputs/`.
