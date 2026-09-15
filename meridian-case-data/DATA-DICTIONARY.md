# Meridian Casualty — data dictionary

Five files, sixty months (2021-01 through 2025-12), forty claims service
centers. All dates are calendar months formatted `YYYY-MM`.

## How the files join

| join | key |
|---|---|
| `applications` → `hires` | `application_id` |
| `applications` → `flex_placements` | `application_id` |
| `applications` → `center_month` | `center_id` and application `month` |
| `hires` → `center_month` | `center_id` and the month appropriate to the question |
| `flex_placements` → `center_month` | `center_id` and the month appropriate to the question |
| any file → `ats_migration` | `center_id` |

Join hires and flex placements to applications using `application_id`; center
and month do not identify an individual. When joining to `center_month`, choose
the date appropriate to the question: application month for conditions when
the application was submitted, `start_month` for conditions when a hire began,
or `placement_month` for conditions when a flex assignment began. `starter.py`
performs the person-level joins and attaches the ATS in use at application.

---

## `applications.csv` — one row per reviewed application

Applications a recruiter reviewed and scored. Most applications Meridian receives
are not individually reviewed; total volume is in
`center_month.applications_received`.

| field | meaning |
|---|---|
| `application_id` | unique |
| `center_id`, `month` | where and when the application was submitted |
| `essay_rubric_score` | 0–30. The three-question situational section, scored by a recruiter on completeness, specificity, organization and apparent care (0–10 per question) |
| `essay_section_minutes` | minutes the applicant spent in the situational section |
| `resume_score` | recruiter's rating of the résumé, standardized |
| `has_adjuster_license` | 1 if the applicant holds an active adjuster license |
| `prior_claims_experience` | 1 if the applicant reports any prior claims work |
| `prior_claims_years` | reported years of prior claims work, rounded to one decimal; 0 if none |
| `referral` | 1 if referred by a current employee |
| `currently_employed` | 1 if employed at the time of application |
| `recruiter_screen_score` | the recruiter's overall screening score |
| `advanced_to_interview` | 1 if the applicant was interviewed |
| `interview_score` | standardized interview rating; blank if not interviewed |
| `outcome` | `hired`, `hired_pending_start`, `offer_declined`, `flex_placement`, or `not_selected` |

`hired_pending_start` means the offer was accepted but the start date falls
after the end of the panel, so there is no row in `hires.csv`.

---

## `hires.csv` — one row per new permanent hire

| field | meaning |
|---|---|
| `hire_id`, `application_id`, `center_id` | identifiers |
| `start_month` | first month on payroll |
| `starting_wage` | hourly starting wage |
| `coaching_hours_first_90d` | supervisor coaching hours logged in the first 90 days |
| `claims_closed_6mo` | claims closed in the first six months |
| `claims_reopened_6mo` | of those, how many were later reopened |
| `reopen_rate_6mo_pct` | reopened as a percentage of closed |
| `retained_6mo` | 1 if still employed six months after starting |
| `separation_month`, `separation_reason` | blank if retained or not yet observed for six months; reason is voluntary, performance or attendance |

**Censoring.** Hires who started in the last six months of the panel have not
yet reached the six-month mark, so `retained_6mo`, the claims fields and the
separation fields are blank for them. These observations are right-censored:
the outcomes do not yet exist, rather than being missing because of a recording
failure.

---

## `flex_placements.csv` — one row per contract placement

Contract claims adjusters supplied through Meridian's staffing partner
and placed on certification, geography and availability.

| field | meaning |
|---|---|
| `placement_id`, `application_id`, `center_id` | identifiers |
| `placement_month` | first month of the assignment |
| `certification_level` | vendor's grading — entry, experienced, licensed |
| `weeks_assigned` | length of the assignment |
| `claims_closed`, `claims_reopened` | volume over the assignment |
| `reopen_rate_pct` | reopened as a percentage of closed |

---

## `center_month.csv` — one row per center per month

The operating panel and the cost inputs for the cost worksheet. The
observational unit is a center-month: each row describes one center in one
month.

| field | meaning |
|---|---|
| `center_id`, `month` | identifiers |
| `ats` | `legacy` or `new` — which applicant tracking system was live that month |
| `openings` | permanent requisitions open |
| `applications_received` | total applications, including those never reviewed |
| `apps_per_opening` | `applications_received` ÷ `openings` |
| `applications_reviewed` | applications a recruiter opened and scored — the rows in `applications.csv` |
| `recruiter_minutes_per_application` | recruiter time per application received |
| `days_to_fill` | average days from requisition to accepted offer |
| `local_unemployment_rate` | percent, local labour market |
| `wage_index` | center wage level, 1.00 = 2021 baseline |

**Cost inputs**, recorded for each center-month and varying across centers and
over time. The field names state the unit:
`recruiter_hourly_rate` and `grader_hourly_rate` are dollars per hour;
`sourcing_cost_per_opening` is dollars per opening;
`training_cost_per_hire` and `ramp_productivity_loss_per_hire` are dollars per
hire; `vacancy_cost_per_day` is dollars per vacancy day;
`separation_cost_per_exit` is dollars per exit; and
`cost_per_reopened_claim` is dollars per reopened claim.
`claims_per_adjuster_6mo` is not a cost: it is the number of claims an adjuster
handles in six months.

---

## `ats_migration.csv` — one row per center

| field | meaning |
|---|---|
| `center_id` | unique center identifier |
| `region` | Meridian operating region |
| `headcount` | center employee count |
| `size_index` | center size relative to the average center |
| `migration_month` | month the center moved to the new ATS; **blank if it never migrated** |
| `migration_wave` | which programme moved it |

**Background on the two systems.** On the **legacy** ATS the situational section
is a session-timed field with paste disabled — answers are typed in one sitting,
in the browser. On the **new** ATS the section is untimed and answers may be
composed anywhere and pasted in. Migration ran in waves: a vendor pilot moved a
small group of centers in 2021, the rollout paused for about eighteen months
during a contract renegotiation, and the full programme ran through 2023 and
2024. Seven centers are still on the legacy system.
