---
id: T2
title: "Discover and classify the items of the sample folder"
layer: "infra"
deps: []
blocks: ["T3", "T5"]
acs: ["AC-12", "AC-15", "AC-17"]
files_hint: ["evals/run_eval.py", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T2 — Discover and classify the items of the sample folder

## Place in the sequence

- **Blocked by:** none (logically independent; physically after T1, which creates the file) · **Blocks:** T3 — Read and validate the known-gap list, T5 — Build the report and the outcome · **Wave:** 1 by dependency, runs after T1 in its lane.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T1, T3, T4, T5, T6, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** a new sample judged by its category band, and an unclassifiable sample reported rather than skipped
> **So that** no sample silently drops out of the check.
>
> — `spec.md §4, US-07, verbatim` · full text: [spec.md](../spec.md)

This task delivers the folder scan that sorts every item into human, AI, unclassified or ignored, so nothing drops out silently.

## Inlined context

> **Flow: validate and classify the sample folder** (read only, nothing persisted). For each item: not a plain text file, or inside a subfolder → mark the item ignored · name starts with `human-` → classify as human · name starts with `ai-` → classify as AI · any other plain text file → mark unclassified and record a failure. After the known-gap step: no samples at all, or no human samples, or no AI samples → record a missing-category failure naming it. Postcondition: every item is classified, unclassified or ignored.
>
> — `sad.md §6, «Flow: validate and classify the sample folder», abridged` · full text: [sad.md](../sad.md)

> **Inputs, Samples:** `evals/samples/` — plain `*.txt` files directly in the folder. `human-` prefix is human, `ai-` prefix is AI, any other plain text file is unclassified. Non-text files and subfolder contents are ignored.
>
> — `contracts/cli.md §3, Samples, verbatim` · full text: [cli.md](../contracts/cli.md)

> **Report completeness (NFR):** 100% of sample files appear in the report, as classified, unclassified or ignored — per-category counts plus ignored items sum to the number of items in the folder.
>
> — `spec.md §6, Report completeness, abridged` · full text: [spec.md](../spec.md)

> **Hard rule:** paths via `pathlib`; samples are processed in sorted name order, with no randomness.
>
> — `sad.md §8, Portability and Determinism, abridged` · full text: [sad.md](../sad.md)

The sample identifier is the file name without `.txt`. Failure kinds are `eval.unclassified_sample` and `eval.missing_category` ([cli.md](../contracts/cli.md) §6). This task takes `--root` as a parameter and does not read the command line (T6 does).

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §5, §6 and [sad.md](../sad.md) §6 in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. Input rules: [cli.md](../contracts/cli.md) §3.

## Acceptance criteria

### AC-12 — error

> **Given** a plain text file in the sample folder whose name does not start with human- or ai-
> **When** the plugin author runs the check
> **Then** the report lists it as unclassified, the run is reported as failed, and the report gives the number of samples per category so a missing sample is visible
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

### AC-15 — error

> **Given** there are no samples at all, or no samples in the human category, or none in the AI category
> **When** the plugin author runs the check
> **Then** the report names the missing category and the run is reported as failed
>
> — `spec.md §5, AC-15, verbatim` · full text: [spec.md](../spec.md)

### AC-17 — happy path

> **Given** the sample folder also contains files that are not plain text files, or items inside subfolders
> **When** the plugin author runs the check
> **Then** the report lists them as ignored and they do not change the outcome
>
> — `spec.md §5, AC-17, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `classify_folder(samples_dir)` in `evals/run_eval.py` returning human, AI, unclassified and ignored lists, sorted by name, plus the folder item total.
- [ ] Add `missing_categories(classified)` returning the names of absent categories (`"samples"` when the folder is empty).
- [ ] Tests in `evals/tests/test_run_eval.py` building a temporary folder with each kind of item: counts plus ignored equal the item total.

## Edge cases

| Case | Behaviour |
|---|---|
| `notes.txt` (no prefix) | unclassified, failure `eval.unclassified_sample` naming it |
| `human-x.md`, `ai-y.png` | ignored (not plain text), no failure |
| `.txt` file inside a subfolder | ignored; the subfolder is one ignored item |
| Folder with only human samples | `eval.missing_category` naming the AI category |
| Empty folder or missing folder | `eval.missing_category` for the whole set, never a crash |
| `Human-x.txt` (capital H) | unclassified (prefix match is exact) |

## Definition of Done

- [ ] Unit tests for classified, unclassified, ignored and missing-category cases pass.
- [ ] Per-category counts plus ignored equal the number of items in the folder in every test folder.
- [ ] Order of results is sorted by name regardless of file system order.
