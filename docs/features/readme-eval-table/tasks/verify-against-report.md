---
id: T5
title: "Compare the table with the report and prepare the pull request"
layer: "docs"
deps: ["T3", "T4"]
blocks: []
acs: ["AC-08"]
files_hint: ["README.md", "CONTEXT.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "review"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T5 — Compare the table with the report and prepare the pull request

## Place in the sequence

- **Blocked by:** T3 — Fill the result cells with the six-value mapping, T4 — Add the caption and the notes · **Blocks:** none · **Wave:** 4, last: it checks the finished README.
- **Lane:** shares `README.md` and `CONTEXT.md` with the earlier tasks, but runs after all of them. It changes a file only to fix a difference it finds.

## Why (user story)

> **As a** plugin author
> **I want** to refresh the table from one eval report so that it matches the report, shows failures as failures and excuses only samples I flagged
> **So that** the README never shows a broken detector as healthy.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task is the reviewer comparison of table and report, and the footprint, rendering and glossary checks before merge.

## Inlined context

> **Accuracy** — 100% of table cells (category, known-gap status, index, result) equal the report of the run named in the caption. Measured: the plugin author pastes the report output into the pull request description and the reviewer compares the table with it before the change is merged.
> **Completeness** — 100% of the human and AI samples the report lists appear as rows; per-category row counts equal the report's summary. Measured: compare counts before merge.
> **Rendering** — 1 table, 6 columns, plain markdown with 0 HTML. Measured: open the rendered README before merge.
> **Footprint** — 2 files changed outside the docs folder (the README and the glossary file), 0 code files. Measured: diff of the change.
>
> — `spec.md §6, NFR table, abridged` · full text: [spec.md](../spec.md)

> Eval table — the table in the project README that lists every sample with its category, expected band, known-gap status, the index of the last run and the result of the row, with a caption naming the plugin copy and the run date and a note on how far the human evidence reaches […]
>
> — `CONTEXT.md, Glossary, Eval table, abridged` (added in commit 8f3d89e) · full text: [CONTEXT.md](../../../../CONTEXT.md)

> The reviewer compares every cell with the pasted report before merge (QG-1). Conventional commit prefix `docs:`.
>
> — `sad.md §2 and §11, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** 0 code files change; the eval runner, the detector, the bands and the sample set are not changed.
>
> — `spec.md §3 and §6 Footprint, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-08 — cross-context: the table equals the eval report

> **Given** the plugin author has the report of one eval run
> **When** the plugin author refreshes the eval table
> **Then** each row's category, known-gap status, index and result equal the report, the rows are exactly the samples the report lists, and the per-category counts (human and AI) equal the report's summary
> **And** the result of a row is derived from the report as follows: the row verdict plus the report section that lists the sample, giving one of six values, shown in Ukrainian; an analyzer failure takes precedence over a known-gap flag (the report judges a failed analysis as failed even on a flagged sample), and a drift warning leaves the result «пройдено» — passed («пройдено»), failed: false alarm («провал: хибна тривога»), failed: miss («провал: пропуск»), failed: analyzer failure («провал: збій аналізатора»), known-gap («відомий пропуск, проходити смугу не обов'язково»), gap may be closed («пропуск, можливо, закрито, переглянути мітку»); the categories are shown as «людський» and «ШІ»
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Compare every table row with the T1 report line by line: sample name, category, known-gap status, index, result (via the AC-08 mapping). Zero differences allowed.
- [ ] Compare the row count and the per-category counts with the report's `summary:` line.
- [ ] Check the cross-AC items on the rendered page: bands (25 or below, 26 or above), the caption's plugin and date, the evidence note's N of M, the «Чесна межа» link, no wording as if all passed when a row failed.
- [ ] Open the README as rendered on the repository host (or a markdown preview): 1 table, 6 columns, 0 HTML, Ukrainian wording.
- [ ] `git diff --stat main`: only `README.md` and `CONTEXT.md` outside `docs/`, 0 code files; `CONTEXT.md` carries the «Eval table» term.
- [ ] Paste the T1 report into the pull request description; commit with a `docs:` prefix; record the run date there.

## Edge cases

| Case | Behaviour |
|---|---|
| One cell differs from the report | Fix the cell in `README.md`, repeat the comparison from the start |
| The report changed after T1 (samples edited) | Run again (T1), refresh rows (T2, T3) and note (T4) from the new report |
| The diff touches a code file | Revert it; the change is documentation only |
| Table cannot be read as a table on the host page | Fix the markdown (pipes, header separator) until it renders |

## Definition of Done

- [ ] Table and report show zero differences in category, known-gap status, index, result, row set and per-category counts.
- [ ] The diff touches `README.md` and `CONTEXT.md` outside `docs/`, and no code file.
- [ ] The rendered README shows 1 table of 6 columns with 0 HTML, headers, values, caption and notes in Ukrainian.
- [ ] The pull request description carries the pasted report and the run date.
- [ ] every Hard Rule inlined above still holds
