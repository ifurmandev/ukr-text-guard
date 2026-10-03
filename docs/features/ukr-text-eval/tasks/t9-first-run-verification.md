---
id: T9
title: "Verify the first real run on both shells and update the docs"
layer: "docs"
deps: ["T7", "T8"]
blocks: []
acs: ["AC-01"]
files_hint: ["docs/architecture-map.md", "CONTEXT.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T9 — Verify the first real run on both shells and update the docs

## Place in the sequence

- **Blocked by:** T7 — Make `run.sh` a thin delegate, T8 — Prove independence and repeatability · **Blocks:** none, last task of the epic · **Wave:** 6, needs the finished runner, the delegate and the tests.
- **Lane:** own lane (docs only).

## Why (user story)

> **As a** plugin author
> **I want** to run all samples against expected bands and get a pass/fail report
> **So that** I know whether the detector works.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task delivers the proof that the finished check does what the spec's KPIs and platform NFR ask on the real folder, and brings the repo docs in line with the new command.

## Inlined context

> **Platforms (NFR):** identical verdicts in the plugin author's Windows shell and in a POSIX-compatible shell on the same machine, 2 of 2; a separate Linux or macOS host is not required — one run in each before release.
>
> — `spec.md §6, Platforms, abridged` · full text: [spec.md](../spec.md)

> **KPIs:** False alarms named — 100% of runs name every false alarm, from the first run. Evidence disclosed — 100% of runs state how many human samples reach 150 words. Silent drops — 0 per run (counts plus ignored sum to the folder items). Time to a verdict — at most 60 s in one command.
>
> — `spec.md §7, abridged` · full text: [spec.md](../spec.md)

> **QG-3 how to verify:** the printed duration on the real folder; one run in each shell before release with the verdict lines compared; the diff of the commit that adds a sample leaves the band constants in `run_eval.py` unchanged.
>
> — `sad.md §10, QG-3, abridged` · full text: [sad.md](../sad.md)

> **Stale docs found:** `docs/architecture-map.md` still says the only check is the manual `bash evals/run.sh` that «asserts nothing» and that `evals/run.sh` «hard-codes the guard copy». `CONTEXT.md` Glossary lacks the terms the SAD §12 marks «not yet in CONTEXT.md»: Analyzer failure, Detector copy, Unclassified sample, Inconclusive, Drift warning.
>
> — `docs/architecture-map.md lines 24–26, 65, 109; sad.md §12, abridged` · full text: [sad.md](../sad.md)

The human conclusion on the real run will be inconclusive (2 human samples of 101 and 67 words); that is expected and is a note, not a failure. If the first real run fails a band (for example a human sample above 25), report the finding to the plugin author instead of changing a band, a sample or the detector — those are out of scope (spec §3).

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §6, §7 and [sad.md](../sad.md) §10, §12 in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-01 — happy path

> **Given** a plugin author has samples of both categories and every sample falls within its expected band
> **When** the plugin author runs the check
> **Then** the report lists each sample with its category and index, states that all samples passed, and the run is reported as successful
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Run `python evals/run_eval.py` in PowerShell and `bash evals/run.sh` in Git Bash on the real folder; save both reports in the scratchpad and diff the per-sample and verdict lines (the duration line may differ).
- [ ] Confirm the duration is at most 60 s, the counts plus ignored equal the 10 folder items, and the evidence line states 0 of 2 human samples reach 150 words.
- [ ] Run each of the other two copies once (`--plugin ukr-text-detector`, `--plugin ukr-text-editor`) and confirm each report names its plugin.
- [ ] Update `docs/architecture-map.md` evals entries to describe the new runner, known-gaps list and unit tests; set its reflects commit as that file requires.
- [ ] Add the five missing terms to the `CONTEXT.md` Glossary with the SAD §12 definitions.

## Edge cases

| Case | Behaviour |
|---|---|
| A real sample falls outside its band | the run fails and names it; record the observation for the plugin author, change nothing in bands, samples or detector |
| PowerShell and Git Bash verdict lines differ | stop and report the difference; it breaks the platform NFR |
| Human conclusion inconclusive | expected note, run still exits 0 |
| `ai-engineered-humanity` at index 29 | ordinary AI sample, passes (not in the known-gap list) |

## Definition of Done

- [ ] PowerShell and Git Bash verdict lines are identical (empty diff apart from the duration line).
- [ ] The first-run report names every false alarm if any, the evidence summary and the per-category counts.
- [ ] `docs/architecture-map.md` no longer says the check asserts nothing; `CONTEXT.md` carries the five terms.
- [ ] No band, sample or detector file was changed by this task.
