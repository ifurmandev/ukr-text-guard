---
id: T1
title: "Run the eval on the ukr-text-guard copy and gate on run-level failure"
layer: "docs"
deps: []
blocks: ["T2", "T4"]
acs: ["AC-09b"]
files_hint: ["evals/run.sh"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"
status: "done"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T1 — Run the eval on the ukr-text-guard copy and gate on run-level failure

## Place in the sequence

- **Blocked by:** none · **Blocks:** T2 — Write the eval table header and rows, T4 — Add the caption and the notes · **Wave:** 1, it produces the report every later task copies from.
- **Lane:** own lane. `evals/run.sh` is only run, never edited (spec §3: the runner is not changed). The report and the run date are kept for the pull request description, not committed.

## Why (user story)

> **As a** plugin author
> **I want** to refresh the table from one eval report so that it matches the report, shows failures as failures and excuses only samples I flagged
> **So that** the README never shows a broken detector as healthy.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task fixes the one report the whole refresh is taken from, and refuses to go on when the run itself is broken.

## Inlined context

> The plugin author refreshes the table by hand from the eval report; generating it and checking drift have no roadmap step yet (spec §3, §8).
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> alt run failed at run level (unclassified sample, wrong known-gap list, missing category, missing detector copy, runner error) → Author fixes the cause, runs again; else run finished without a run-level failure → Author writes rows, counts, result mapping, caption with plugin and date, evidence note; pastes the report into the pull request.
>
> A failed row (false alarm, miss, analyzer failure) is a legal input of this flow: it is written as failed with its reason, never softened (spec AC-07, AC-09). Only a run-level failure blocks the refresh (spec AC-09b).
>
> — `sad.md §6, «refresh the table from one run», abridged` · full text: [sad.md](../sad.md)

> **Chosen:** Option 1 [by hand from one report]. It is the only option that keeps the runner untouched and the footprint at 2 files, and the reviewer comparison already covers accuracy for one change.
>
> — `adr/0001-maintain-the-eval-table-by-hand-from-one-report.md, Decision outcome, abridged` · full text: [adr/](../adr/0001-maintain-the-eval-table-by-hand-from-one-report.md)

> **Hard rule:** Accuracy — 100% of table cells (category, known-gap status, index, result) equal the report of the run named in the caption.
>
> — `spec.md §6, Accuracy, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-09b — error: a run that failed as a whole is not published

> **Given** the last run failed at run level although every row passed, for example because of an unclassified sample, a wrong known-gap list, a missing category, a missing detector copy or a runner error (an error other than a failed row)
> **When** the plugin author wants to refresh the eval table
> **Then** the table is not refreshed from that run; the cause is fixed first and the table is taken from a run that finished without a run-level failure
>
> — `spec.md §5, AC-09b, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Run `bash evals/run.sh` from the repo root (default plugin is the ukr-text-guard copy); keep the full report text and the exit code.
- [ ] Note today's calendar date as the run date (the report prints none, spec AC-10).
- [ ] Read the `errors:` section of the report. Any error whose kind is `eval.unclassified_sample`, `eval.bad_known_gap`, `eval.missing_category`, `eval.missing_detector_copy` or `eval.runner_error` is a run-level failure: stop, fix the cause (not in this feature if it needs a code change), run again. `eval.analyzer_failure` is a failed row, not a run-level failure.
- [ ] Confirm the summary line lists 10 samples (human and AI counts match `evals/samples/`); keep the report for T2, T3, T4 and for the pull request description.

## Edge cases

| Case | Behaviour |
|---|---|
| Every row passed but the report has a run-level `errors:` line | No refresh; fix the cause and run again (AC-09b) |
| A row failed (false alarm, miss, analyzer failure) and no run-level error | The report is usable; later tasks write the failed row as failed |
| A sample sits in the folder without a category | `eval.unclassified_sample` — not a sample, run fails, no refresh |
| `known-gaps.txt` flags a human sample or a missing file | `eval.bad_known_gap` — run fails, no refresh |

## Definition of Done

- [ ] A report from a run without a run-level failure is kept, with its exit code and the run date.
- [ ] The report's summary lists the same human and AI sample counts as `evals/samples/`.
- [ ] No file in the repo changed by this task (`git status` shows the same files as before the run).
- [ ] every Hard Rule inlined above still holds
