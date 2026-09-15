---
name: cost-worksheet
description: Compute cost per retained employee exactly as the Meridian finance worksheet in prompt.pdf, pass the worked-example unit test, and lay out the option-comparison table (E19). Use for H10, H11, H12.
---

# The formula (from prompt.pdf, pages 4–6)

```
cost_per_retained = C_hire / r + C_sep * (1/r - 1) + C_policy_retained + [C_quality]
C_hire   = sourcing + training + ramp + days_to_fill * vacancy_cost_per_day  (+ recruiter screening time, see below)
C_quality = claims_per_adjuster_6mo * reopen_rate * cost_per_reopened_claim
```
- `r` = probability a hire is still employed at six months.
- `C_sep` = `separation_cost_per_exit`.
- `C_policy_retained` = any once-per-retained-employee cost of a hypothetical policy (e.g. a
  retention bonus). Zero for the status quo.
- `sourcing` is quoted per opening. If a center-month fills more than one hire per opening,
  divide by hires per opening and state that you did.
- Recruiter screening time per hire = `recruiter_minutes_per_application * applications_received
  / hires * recruiter_hourly_rate / 60`. Include it inside `C_hire` and say so; the worked
  example omits it, so run the unit test without it.

# Unit test (must pass before any costing is reported)
Using 2025 average rates across all center-months, with r = 0.75, days_to_fill = 30,
reopen = 0.06:
- `C_hire` ≈ 747 + 5,085 + 6,540 + 30 × 219 ≈ $18,942
- hiring + separation cost ≈ 18,942 / 0.75 + 2,540 × (1/0.75 − 1) ≈ $26,103
- quality cost ≈ 609 × 0.06 × 323 ≈ $11,800
Tolerance: within 2 % (the prompt rounded its inputs). Print the test result at the top of
`analysis/08_cost_worksheet.py` output and fail loudly if it does not pass.

# Inputs by scenario
- Status quo: 2025 new-ATS center-months for rates; observed r, days_to_fill and reopen from
  hires applying under the new ATS in the AI era (state the cohort window and its censoring).
- Counterfactual A (essay still works, same era): 2024–25 legacy-center hires.
- Counterfactual B (pre-AI new ATS): 2021–22 new-ATS hires, costed at 2025 rates.
- Each policy option: state r, days_to_fill, reopen, and any C_policy as explicit assumptions
  with a one-line defence, then vary them in E20.

# E19 table layout
| option | r | days to fill | reopen % | C_hire | C_sep term | C_policy | C_quality | CPR excl. quality | CPR incl. quality | Δ vs status quo | annual Δ at 2025 hiring volume |

Annual volume = retained hires per year in the relevant centers (use actual 2025 hire counts,
not the "20 per center per month" rule of thumb, and show both).

# Sensitivity (E20)
Vary one input at a time for the recommended option: r (low/base/high from the estimated
range), days_to_fill change (0, +5, +10, +15), reopen change, monetise quality yes/no,
implementation cost. Report break-even values: extra vacancy days that erase the gain; the r
improvement a given retention bonus needs.
