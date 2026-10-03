---
id: T2
title: "Replace the README sample table with the eval table header and rows"
layer: "docs"
deps: ["T1"]
blocks: ["T3"]
acs: ["AC-01", "AC-02"]
files_hint: ["README.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T2 — Replace the README sample table with the eval table header and rows

## Place in the sequence

- **Blocked by:** T1 — Run the eval and gate on run-level failure · **Blocks:** T3 — Apply the result mapping to the rows · **Wave:** 2, needs the report from T1.
- **Lane:** shares `README.md` with T3 and T4 — serialized, order T2 → T3 → T4.

## Why (user story)

> **As a** text author
> **I want** every sample listed with its expected band and the index it got
> **So that** I can judge from the README how the detector behaves without running it.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task builds the skeleton of the table: header, one row per sample, category, band, index and per-category counts.

## Inlined context

> The committed approach is to replace the README sample table with an eval table: one row per sample with its category, expected band, known-gap status, the index of the last run and the result of the row [...]
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> README.md — section «Перевірка»: intro line, eval table, caption, notes (old table replaced).
>
> — `sad.md §5, internal decomposition, abridged` · full text: [sad.md](../sad.md)

> Restructuring or translating the README — only the sample table area changes: the table, its caption and the notes beside it. The `bash evals/run.sh` block stays as it is, and the one intro line of the check section may be reworded only to fit the caption.
>
> — `spec.md §3, non-goals, verbatim` · full text: [spec.md](../spec.md)

> **Hard rule:** Rendering — 1 table, 6 columns, plain markdown with 0 HTML, shown as a table on the repository host page. Language — 100% of the table headers, the cell values (category, known-gap status, result), the caption and the notes in Ukrainian, like the rest of the README.
>
> — `spec.md §6, Rendering and Language, abridged` · full text: [spec.md](../spec.md)

> the categories are shown as «людський» and «ШІ»
>
> — `spec.md §5, AC-08, verbatim (fragment)` · full text: [spec.md](../spec.md)

Column count note (derived, not quoted): AC-01 names five cell kinds (category, band, known-gap status, index, result) and §6 Rendering fixes 6 columns, so the sixth is the sample name.

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-01 — happy path

> **Given** a text author opens the project README
> **When** the text author reads the eval table
> **Then** the table lists every sample of the check set, each with its category (human or AI), its expected band, its known-gap status, the index it got in the last run and the result of the row, and states how many samples there are per category
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-02 — happy path

> **Given** the eval table lists a human sample and an ordinary AI sample
> **When** the text author reads their expected bands
> **Then** the human sample shows a band of 25 or below and the ordinary AI sample shows a band of 26 or above, the same bands the eval judges against; a known-gap AI sample shows the AI band too (26 or above) and its exemption is stated in its result (AC-03)
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] In `README.md` section «Перевірка», delete the old 3-column table (Зразок / Очікування / Індекс); keep the `bash evals/run.sh` block as it is.
- [ ] Write a header of 6 Ukrainian columns: sample, category, expected band, known-gap, index, result. Use the sample names exactly as the report prints them.
- [ ] Add one row per sample the report lists (10 rows). Fill category («людський» / «ШІ»), band («25 або менше» for human, «26 або більше» for AI, known-gap included), known-gap status and the index copied from the report; leave the result cell to T3.
- [ ] State the per-category counts in a line near the table (human and AI), equal to the report's summary line.
- [ ] Reword the section's intro line only if the caption (T4) needs it; no other README text changes.

## Edge cases

| Case | Behaviour |
|---|---|
| A sample ignored or unclassified in the folder | Not a row (spec §6 Completeness); an unclassified file fails the run, T1 stops it |
| A known-gap AI sample | Band is the AI band (26 or above), same as any AI sample; the exemption goes to the result cell in T3 |
| An analyzer failure on a row | Index cell shows a dash (T3 owns the wording; the report prints no index) |
| Old table cells | Gone entirely; the old «ШІ + обфускація» / «ШІ під людину» wording is not carried over |

## Definition of Done

- [ ] The old 3-column table is gone; one 6-column table of plain markdown with 0 HTML is in its place.
- [ ] Row set equals the report's sample list and the per-category counts equal the report's summary.
- [ ] Human rows read a band of 25 or below, AI rows 26 or above.
- [ ] every Hard Rule inlined above still holds
- [ ] README renders the table on the repository host page (preview before commit)
