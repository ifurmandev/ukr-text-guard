---
id: T5
title: "Build the report, the evidence summary and the outcome decision"
layer: "app"
deps: ["T1", "T2", "T3", "T4"]
blocks: ["T6"]
acs: ["AC-01", "AC-02", "AC-07", "AC-08", "AC-19"]
files_hint: ["evals/run_eval.py", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "done"
---

# T5 — Build the report, the evidence summary and the outcome decision

## Place in the sequence

- **Blocked by:** T1 — judging function, T2 — classify items, T3 — known-gap list, T4 — analyse one sample · **Blocks:** T6 — CLI entry point · **Wave:** 3, joins the four building blocks into the use case.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T1, T2, T3, T4, T6, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** each sample's word count and reliability, and an inconclusive mark on the human conclusion when samples are short
> **So that** I do not take a green run on very short texts as proof.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

> **As a** plugin author
> **I want** to run all samples against expected bands and get a pass/fail report
> **So that** I know whether the detector works.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task delivers the use case `run_check(root, plugin) -> (report_text, failed)`: it runs the earlier pieces over every sample and prints the facts the contract lists.

## Inlined context

> **Flow: summarise the evidence and signal the outcome.** Count samples per category plus ignored items and compare with the folder total. Count human samples that reach 150 words by the analyzer's own word count; if fewer than all do, mark the human conclusion inconclusive as a note. List every known-gap sample with its reason. Gather notes: drift, gap may be closed, inconclusive, hidden characters. Print the report with each word count and reliability, the evidence summary and the duration. Any failure — analyzer failure, false alarm, miss, unclassified item, bad known-gap entry, missing category or missing detector copy — means failed. Only notes or nothing at all means passed.
>
> — `sad.md §6, «Flow: summarise the evidence and signal the outcome», abridged` · full text: [sad.md](../sad.md)

> **Output sections, in this order:** 1 header (plugin used) · 2 per-sample lines in sorted name order (name, category — human, AI or known-gap AI —, index, word count, reliability, verdict; a failure line shows the reason instead of an index) · 3 false alarms · 4 misses · 5 errors (each naming the item and the reason) · 6 known-gap list with reasons · 7 notes (drift, gap may be closed, hidden-character, inconclusive; never change the outcome) · 8 summary (per-category counts, ignored items, sum check against the folder total, how many ordinary AI samples reach 51, how many human samples reach 150 words out of how many, the duration, the verdict line). A failing run still prints the whole report. The contract fixes which facts appear, not the wording.
>
> — `contracts/cli.md §4, Output, abridged` · full text: [cli.md](../contracts/cli.md)

> **Hard rule (Determinism):** samples in sorted name order, no randomness, no timestamps in the report except the duration line.
>
> — `sad.md §8, Determinism, abridged` · full text: [sad.md](../sad.md)

> **Hard rule (Encoding and Internationalisation):** the runner reconfigures its own stdout to UTF-8 with `errors="replace"`; the report is English prose, sample names and analyzer text pass through untouched.
>
> — `sad.md §8, Encoding and Internationalisation, abridged` · full text: [sad.md](../sad.md)

> **Hard rule (NFR):** one run over up to 50 samples takes at most 60 s, shown by the duration printed in the report.
>
> — `spec.md §6, Run time, abridged` · full text: [spec.md](../spec.md)

> **Decision (ADR-0002):** the outcome is one success-or-failure signal; warnings, drift notes and the inconclusive mark never change it.
>
> — `adr/0002, Decision drivers, abridged` · full text: [adr/](../adr/0002-signal-the-outcome-by-exit-code-only.md)

Uses T1 `judge()`, T2 `classify_folder()`, T3 `apply_known_gaps()`, T4 `analyze_sample()`. The hidden-character note is printed only for samples that contain such characters and says a high index may come from the file rather than the text (spec §8 OQ-3 default). T5 does not parse arguments, resolve the detector copy path or set the process exit code (T6).

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §5, [sad.md](../sad.md) §6, §8 and [cli.md](../contracts/cli.md) §4 in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. The report layout is [cli.md](../contracts/cli.md) §4.

## Acceptance criteria

### AC-01 — happy path

> **Given** a plugin author has samples of both categories and every sample falls within its expected band
> **When** the plugin author runs the check
> **Then** the report lists each sample with its category and index, states that all samples passed, and the run is reported as successful
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-02 — happy path

> **Given** the ordinary AI samples have indexes of various levels
> **When** the plugin author runs the check
> **Then** the report states how many ordinary AI samples reach the high level (51 or more) for information, and this count never changes whether the run passes
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — authorization: only an explicit entry by the plugin author excuses a sample

> **Given** a sample without an explicit known-gap entry by the plugin author falls outside its band
> **When** the plugin author runs the check
> **Then** the report does not excuse it, and the report lists every known-gap sample so each excused sample is visible
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

This task owns the second half (the known-gap list in every report); T1 owns the first half.

### AC-08 — domain invariant: short evidence is never stated as conclusive

> **Given** any set of samples
> **When** the plugin author runs the check
> **Then** the report shows each sample's word count and reliability, both taken from the analyzer's own count and rating, states how many human samples reach 150 words out of how many, and marks the human conclusion as inconclusive whenever fewer than all of them do
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

### AC-19 — domain invariant: notes never change the outcome

> **Given** a run in which no sample fails but the human conclusion is inconclusive, or a drift warning or a gap-may-be-closed warning is shown
> **When** the run ends
> **Then** the run is reported as successful, because inconclusive marks and warnings are notes and never change whether a run passes
>
> — `spec.md §5, AC-19, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `run_check(root, plugin_analyzer_path)` in `evals/run_eval.py` that classifies the folder, applies the known-gap list, analyses each sample in sorted order, judges it and collects verdicts, errors and notes.
- [ ] Add `render_report(...)` producing the eight sections in the order of the contract, with the plugin name, duration and verdict line; `failed` is true if any error list or any failed verdict is non-empty.
- [ ] Add the evidence summary: per-category counts plus ignored equal folder total, ordinary-AI count at 51 or more, human samples at 150 words or more out of the human total, inconclusive note.
- [ ] Add the known-gap list section (name and reason) and the hidden-character note.
- [ ] Tests in `evals/tests/test_run_eval.py` with a fake analyzer that returns an index per sample name: all-pass, false alarm, miss, drift only, inconclusive only, gap-may-be-closed only, mixed.

## Edge cases

| Case | Behaviour |
|---|---|
| Run with only notes (drift, inconclusive, gap may be closed) | `failed` false, verdict line «passed» |
| Any one failure kind present | `failed` true, the whole report still printed |
| All human samples under 150 words | «0 of N reach 150 words, human conclusion inconclusive» |
| No human sample reaches 150 words but N = 0 | handled by the missing-category error, no division |
| Known-gap sample at index below 26 | listed in the known-gap section, no warning |
| Analyzer failure line | shows the reason where the index would be; no index is printed |
| Two runs on the same inputs | reports differ only in the duration line |

## Definition of Done

- [ ] Report tests for AC-01, AC-02, AC-07, AC-08 and AC-19 pass against a fake analyzer.
- [ ] A test asserts that a run with notes only yields `failed == False`.
- [ ] A test asserts that two reports of the same inputs differ only in the duration line.
- [ ] Every Hard Rule inlined above still holds (sorted order, UTF-8, no timestamps).
