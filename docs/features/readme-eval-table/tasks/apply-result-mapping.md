---
id: T3
title: "Fill the result cells with the six-value mapping, known-gap and failed rows"
layer: "docs"
deps: ["T2"]
blocks: ["T5"]
acs: ["AC-03", "AC-04", "AC-07", "AC-08", "AC-09"]
files_hint: ["README.md"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "done"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T3 — Fill the result cells with the six-value mapping, known-gap and failed rows

## Place in the sequence

- **Blocked by:** T2 — Replace the README sample table with the eval table header and rows · **Blocks:** T5 — Compare the table with the report and prepare the pull request · **Wave:** 3, needs the rows from T2.
- **Lane:** shares `README.md` with T2 and T4 — serialized, order T2 → T3 → T4.

## Why (user story)

> **As a** plugin author
> **I want** to refresh the table from one eval report so that it matches the report, shows failures as failures and excuses only samples I flagged
> **So that** the README never shows a broken detector as healthy.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task writes the result of every row from the report, so a known miss is explained and a failure is never softened.

## Inlined context

> A failing sample is shown as failed with its reason, never softened.
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> Result mapping — six fixed values from the row verdict plus the report section; analyzer failure beats a known-gap flag; a drift warning leaves «пройдено».
> Known-gap authority — only the plugin author's flag in `evals/known-gaps.txt` excuses a sample; a human sample is never known-gap.
>
> — `sad.md §8, crosscutting concepts, abridged` · full text: [sad.md](../sad.md)

> Showing drift warnings or hidden-character and encoding notes of the report in the table — they stay in the report; the table shows only the result of each row and the one evidence note (AC-05).
> Copying the reason the plugin author recorded for a known-gap flag into the table — the row says only that passing the band is not required (AC-03).
>
> — `spec.md §3, non-goals, verbatim` · full text: [spec.md](../spec.md)

> **Hard rule:** A failing sample relabelled known-gap in the table to look healthy: the row is judged against the flag list the plugin author keeps, not against the table (AC-09).
>
> — `spec.md §6.1, abuse cases, verbatim` · full text: [spec.md](../spec.md)

> **Hard rule:** Language — the cell values (category, known-gap status, result) are in Ukrainian; Accuracy — 100% of cells equal the report.
>
> — `spec.md §6, Language and Accuracy, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-03 — happy path

> **Given** the plugin author has flagged an AI sample as known-gap
> **When** the text author reads that sample's row
> **Then** the row is marked as known-gap, its result says that passing its band is not required, and it shows the index it got, so a low index on that sample is visible and explained rather than hidden
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-04 — domain invariant: a gap that may be closed is flagged

> **Given** a known-gap sample received an index of 26 or above in the last run
> **When** the text author reads its row
> **Then** the result of the row says the gap may be closed and the label should be reviewed, instead of showing it as an ordinary pass
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — error

> **Given** the last run failed because a human sample is a false alarm, an ordinary AI sample is a miss, or the analyzer failed on a sample
> **When** the plugin author refreshes the eval table from that run
> **Then** the result of the affected row says failed with its reason (false alarm, miss or analyzer failure), the row shows its index for a false alarm and a miss and a dash for an analyzer failure (the report prints no index for that row; when the failure is an index outside 0 to 100, the number appears only in the failure reason), and the table is not worded as if every sample passed
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — cross-context: the table equals the eval report

> **Given** the plugin author has the report of one eval run
> **When** the plugin author refreshes the eval table
> **Then** each row's category, known-gap status, index and result equal the report, the rows are exactly the samples the report lists, and the per-category counts (human and AI) equal the report's summary
> **And** the result of a row is derived from the report as follows: the row verdict plus the report section that lists the sample, giving one of six values, shown in Ukrainian; an analyzer failure takes precedence over a known-gap flag (the report judges a failed analysis as failed even on a flagged sample), and a drift warning leaves the result «пройдено» — passed («пройдено»), failed: false alarm («провал: хибна тривога»), failed: miss («провал: пропуск»), failed: analyzer failure («провал: збій аналізатора»), known-gap («відомий пропуск, проходити смугу не обов'язково»), gap may be closed («пропуск, можливо, закрито, переглянути мітку»); the categories are shown as «людський» and «ШІ»
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — authorization: only the plugin author's explicit flag excuses a sample

> **Given** a sample is outside its expected band and the plugin author has not flagged it as known-gap
> **When** the plugin author refreshes the eval table
> **Then** the row is shown as failed and not as known-gap, and a human sample is never shown as known-gap
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] For each sample, find it in the report: its row line gives `passed` / `failed` / `analyzer failure`; the sections `false alarms`, `misses`, `known-gap samples` and the `notes` line `gap may be closed` decide which of the six values applies.
- [ ] Write the result cell in `README.md` using exactly the six Ukrainian values from AC-08; an analyzer failure beats a known-gap flag.
- [ ] Known-gap row: write «відомий пропуск, проходити смугу не обов'язково» and keep its index; do not copy the reason from `evals/known-gaps.txt`. If the report notes `gap may be closed` for it, write «пропуск, можливо, закрито, переглянути мітку» instead.
- [ ] Failed row (false alarm or miss): keep its index and write the failure value. Analyzer failure: index cell is a dash, the number (if outside 0 to 100) appears only in the failure reason.
- [ ] Do not add drift, hidden-character or encoding notes to any cell; a drift warning leaves «пройдено».
- [ ] Do not mark any sample known-gap unless `evals/known-gaps.txt` lists it; never on a human row.

## Edge cases

| Case | Behaviour |
|---|---|
| Analyzer failure on a flagged known-gap sample | «провал: збій аналізатора», index a dash, not known-gap |
| Drift warning on a human sample | Result stays «пройдено», warning not shown in the table |
| Known-gap sample at index 26 or above | «пропуск, можливо, закрито, переглянути мітку», not an ordinary pass |
| Out-of-band sample not in `known-gaps.txt` | «провал: хибна тривога» (human) or «провал: пропуск» (AI), never known-gap |
| Every row passed in this run | Table is worded plainly; no failure text invented |
| At least one row failed | The table (and the text near it, T4) is not worded as if every sample passed |

## Definition of Done

- [ ] Every result cell is one of the six AC-08 values and matches the report line for that sample.
- [ ] The only known-gap row(s) are those in `evals/known-gaps.txt`; no human row is known-gap.
- [ ] A failed row (if the run has one) shows its reason, and a dash for an analyzer failure.
- [ ] every Hard Rule inlined above still holds
- [ ] README still renders one 6-column table with 0 HTML
