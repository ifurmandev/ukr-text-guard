---
id: T4
title: "Run the check and verify the verdict"
layer: "tests"
deps: ["T3"]
blocks: ["T5", "T6"]
acs: ["AC-03", "AC-04", "AC-12"]
files_hint: ["docs/features/human-corpus/eval-report.txt", "evals/run.sh"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"   # measured 50 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T4 — Run the check and verify the verdict

## Place in the sequence

- **Blocked by:** T3 — Add the sample files and remove the two short ones · **Blocks:** T5 — Refresh the README table and caption, T6 — Write the changelog note · **Wave:** 4, needs the sample files.
- **Lane:** own lane.

## Why (user story)

> **As a** plugin author
> **I want** human samples of 150 words or more from at least three authors, at least one of them another person
> **So that** the eval no longer marks the human conclusion as inconclusive.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

> **As a** plugin author
> **I want** a human sample the detector wrongly flags to stay in the set and show as a false alarm
> **So that** the real rate of false accusations is not hidden by removing awkward texts.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task runs the eval once, keeps the report as the input for T5 and T6, and checks the verdict against the criteria. A red run caused by a false alarm is a valid result, not a defect to fix.

## Inlined context

> **Flow B:** the user runs the check; the eval analyses every sample. A human sample above the band is listed as a false alarm, the run fails, the sample stays with no excuse path. A human sample below 150 words marks the human conclusion inconclusive and the step is not reported as done. When all reach 150 words the report says so, and the user counts at least three authors with one other person in the register.
>
> — `sad.md §6, Flow B, abridged` · full text: [sad.md](../sad.md)

> **Bands:** human band 25, drift above 15, reliable length 150 words. Known-gap can never be put on a human sample.
>
> — `sad.md §2, Technical constraints, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** detector, eval and bands are untouched; a human sample above 25 fails the run and stays in the set.
>
> — `sad.md §4, strategic choice 4, abridged` · full text: [sad.md](../sad.md)

> **NFR:** full run ≤ 60 s for up to 30 samples; two runs on the same files give the same index and verdict.
>
> — `spec.md §6, Duration and Reproducibility rows, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-03 (US-03) — happy path

> **Given** the check set holds human samples from at least three authors and every human sample reaches 150 words
> **When** the plugin author runs the check
> **Then** the report states that all human samples reach 150 words, does not mark the human conclusion as inconclusive, and the register lists at least three authors, at least one of them another person
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-04 (US-04) — error

> **Given** a new human sample receives an index above the human band of 25
> **When** the plugin author runs the check
> **Then** the report lists the sample as a false alarm and the run is reported as failed, the sample stays in the set and in the README table as a false alarm, and nobody removes it or excuses it
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-12 (US-03) — error

> **Given** a human sample of fewer than 150 words is in the set
> **When** the plugin author runs the check
> **Then** the report marks the human conclusion as inconclusive and the README note says so, and the step is not reported as done
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Run `bash evals/run.sh` on the `ukr-text-guard` copy; save the full report, the exit code and the run date to `docs/features/human-corpus/eval-report.txt`.
- [ ] Check: all human samples at 150 words or more, no «inconclusive» line, duration ≤ 60 s.
- [ ] Read the register: at least 3 authors, at least 1 another person.
- [ ] Run `git log --oneline -- evals/samples` and confirm the register commit precedes the sample commit; note the result in the report file.
- [ ] If a human sample is a false alarm: note it in the report file as a known limitation; do not touch the sample.
- [ ] Run a second time and confirm identical indexes.

## Edge cases

| Case | Behaviour |
|---|---|
| False alarm on a human sample | Report lists it, exit 1, work continues to T5 with the false alarm shown; sample untouched (AC-04). |
| A human sample below 150 words | Report says inconclusive; the step is not done; go back to T2/T3 only for a length reason (AC-12, AC-06). |
| Run slower than 60 s | Record the duration in the report file as a finding. |

## Definition of Done

- [ ] `eval-report.txt` holds the report, exit code, date and the `git log` order check.
- [ ] The verdict matches AC-03, AC-04 or AC-12 as observed; no sample or eval file changed in this task.
- [ ] Two runs give the same indexes.
- [ ] Every Hard Rule inlined above still holds.
