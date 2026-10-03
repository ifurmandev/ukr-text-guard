---
id: T1
title: "Add the pure judging function and the band constants"
layer: "domain"
deps: []
blocks: ["T5"]
acs: ["AC-03", "AC-04", "AC-05", "AC-06", "AC-07"]
files_hint: ["evals/run_eval.py", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T1 — Add the pure judging function and the band constants

## Place in the sequence

- **Blocked by:** none · **Blocks:** T5 — Build the report and the outcome · **Wave:** 1, creates `evals/run_eval.py` and the shared types every later task uses.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T2, T3, T4, T5, T6, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** human samples above their band listed separately
> **So that** I can see when the detector accuses a person.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

> **As a** text author
> **I want** the check to fail whenever a human sample is labelled suspicious
> **So that** the detector is not shipped with false accusations of people.
>
> — `spec.md §4, US-08, verbatim` · full text: [spec.md](../spec.md)

This task delivers the rule that turns one analyzed sample into a verdict, with no I/O, so every band and every flag branch is testable without a process.

## Inlined context

> A human sample must stay at 25 or below (with a warning above 15), an ordinary AI sample must reach 26 or above (and a count reaching 51 or above is reported for information only). Known-gap is a flag, not a third category, and only an AI sample can carry it … a flagged sample never fails a run and only warns when its index reaches the AI band of 26, meaning the gap may be closed.
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> **Flow: judge one sample.** A pure step with no I/O. Inputs: category, known-gap flag, analysis or failure.
> - analyzer failure → verdict failed, with the failure reason, never a low index
> - human sample, with or without a flag: index above 25 → failed, listed separately as a false alarm · index above 15 → passed, drift warning naming the sample · index 15 or below → passed
> - ordinary AI sample without a flag: index below 26 → failed, listed as a miss · index 26 or above → passed, and at 51 or above counted as high level for information only
> - known-gap AI sample: index 26 or above → passed, warning that the gap may be closed · index below 26 → passed, listed as a known-gap
> - postcondition: only an explicit flag on an AI sample excuses a sample, and a flag never turns a failure into a pass
>
> — `sad.md §6, «Flow: judge one sample», abridged` · full text: [sad.md](../sad.md)

> Bands and limits are named constants in `run_eval.py`: human max 25, human drift warning above 15, AI min 26, informational high level 51, reliable length 150 words, 10 s per sample.
>
> — `sad.md §8, Configuration, abridged` · full text: [sad.md](../sad.md)

> **Decision (ADR-0001):** Category comes from the file name prefix, the bands are named constants in `evals/run_eval.py`, and known-gap is an explicit line in `evals/known-gaps.txt`.
>
> — `adr/0001, Decision outcome, abridged` · full text: [adr/](../adr/0001-keep-known-gaps-in-a-plain-list-file.md)

> **Hard rule:** Python 3, standard library only; the repo pins no minimum version and the author runs 3.12.10, so avoid version-specific syntax.
>
> — `sad.md §2, Technical, abridged` · full text: [sad.md](../sad.md)

**Shared interface this task fixes for T2–T6** (names are the contract between tasks; failure kinds are the labels of `contracts/cli.md §6`):

- Constants: `HUMAN_MAX=25`, `HUMAN_DRIFT_ABOVE=15`, `AI_MIN=26`, `HIGH_LEVEL=51`, `RELIABLE_WORDS=150`, `SAMPLE_TIMEOUT_S=10`, `DEFAULT_PLUGIN="ukr-text-guard"`.
- `Analysis(index, words, reliability)` and `Failure(reason)` — the two possible outcomes of analysing a sample.
- `judge(category, known_gap, outcome) -> Verdict(passed, kind, note, high_level)` with `category` in `"human"` / `"ai"`, `kind` in `None` / `"eval.false_alarm"` / `"eval.miss"` / `"eval.analyzer_failure"`, `note` in `None` / `"drift"` / `"gap_may_be_closed"` / `"known_gap"`.

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §1, §5 and [sad.md](../sad.md) §6, §8 in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. Failure-kind labels come from [cli.md](../contracts/cli.md) §6.

## Acceptance criteria

### AC-03 — error

> **Given** a human sample receives an index above the human band of 25
> **When** the plugin author runs the check
> **Then** the report lists that sample separately as a false alarm with its name and index, and the run is reported as failed
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-04 — happy path

> **Given** a human sample receives an index above 15 and within the human band of 25
> **When** the plugin author runs the check
> **Then** the report warns about drift and names the sample, and the run still passes
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-05 — error

> **Given** an ordinary AI sample receives an index below the AI band of 26
> **When** the plugin author runs the check
> **Then** the report lists that sample as a miss with its name and index, and the run is reported as failed
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-06 — domain invariant: a known-gap sample never fails a run

> **Given** a known-gap sample receives an index of 26 or above
> **When** the plugin author runs the check
> **Then** the report warns that the gap may be closed and the label should be reviewed, and the run is not failed because of that sample
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — authorization: only an explicit entry by the plugin author excuses a sample

> **Given** a sample without an explicit known-gap entry by the plugin author falls outside its band
> **When** the plugin author runs the check
> **Then** the report does not excuse it, and the report lists every known-gap sample so each excused sample is visible
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

This task owns the first half (no excuse without a flag); T5 owns the known-gap list in the report.

## Checklist

- [ ] Create `evals/run_eval.py` with the constants and the `Analysis`, `Failure`, `Verdict` types listed above.
- [ ] Implement `judge()` per the flow, exactly the boundaries 15/16, 25/26, 50/51.
- [ ] Create `evals/tests/test_run_eval.py` (unittest) with a table test per band boundary, for human, ordinary AI and known-gap AI.

## Edge cases

| Case | Behaviour |
|---|---|
| Human index 25 | passed, drift note |
| Human index 26 | failed, `eval.false_alarm` |
| Human index 15 / 16 | passed with no note / passed with drift note |
| Human sample with the known-gap flag | judged against the human band as usual (the flag is an error reported by T3, never an excuse) |
| Ordinary AI index 25 / 26 | failed `eval.miss` / passed |
| Ordinary AI index 51 | passed, `high_level` true |
| Known-gap AI index 9 | passed, note `known_gap` |
| Known-gap AI index 26 or more | passed, note `gap_may_be_closed`, never failed |
| Known-gap AI sample whose analysis is a `Failure` | failed `eval.analyzer_failure` (a flag never turns a failure into a pass) |

## Definition of Done

- [ ] Boundary table tests for all three sample kinds pass (`python -m unittest discover evals/tests`).
- [ ] `judge()` has no I/O and no import beyond the standard library.
- [ ] A flag never turns any failed verdict into a passed one (test).
- [ ] The constants are the only place the bands appear.
