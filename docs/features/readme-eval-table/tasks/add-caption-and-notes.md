---
id: T4
title: "Add the caption, the evidence note and the pointer to «Чесна межа»"
layer: "docs"
deps: ["T1"]
blocks: ["T5"]
acs: ["AC-05", "AC-05b", "AC-06", "AC-10"]
files_hint: ["README.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T4 — Add the caption, the evidence note and the pointer to «Чесна межа»

## Place in the sequence

- **Blocked by:** T1 — Run the eval and gate on run-level failure · **Blocks:** T5 — Compare the table with the report and prepare the pull request · **Wave:** 2 by dependencies, but it shares `README.md`.
- **Lane:** shares `README.md` with T2 and T3 — serialized, so it runs after T3 (order T2 → T3 → T4). It needs only T1's report and run date, not T2's rows.

## Why (user story)

> **As a** text author
> **I want** the table to say how many human samples are long enough to count
> **So that** I do not read a clean result on very short texts as proof that the detector never accuses a person.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

> **As a** plugin author
> **I want** the table to name the plugin copy measured and the date of the run
> **So that** a reader and I can tell how stale it is.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task writes everything around the table: the caption with plugin and date, the evidence note and the pointer that the index is not proof.

## Inlined context

> a caption that names the plugin copy measured and the date of the run, and a note beside it that states how far the evidence reaches. In the first run both human samples are short (67 and 101 words, below the 150 words under which the analyzer marks its statistics as low («текст закороткий»)), so the human conclusion is inconclusive and the table must say so rather than read as proof.
>
> — `spec.md §1, committed approach, abridged` · full text: [spec.md](../spec.md)

> Evidence limit — a note states how many human samples reach 150 words out of how many. Run identity — the caption names the plugin copy and the calendar date of the run.
>
> — `sad.md §8, crosscutting concepts, abridged` · full text: [sad.md](../sad.md)

> Evidence note — the note beside the table that states how many human samples reach 150 words, the point under which the analyzer marks its statistics as low.
>
> — `sad.md §12, glossary, Evidence note, verbatim` · full text: [sad.md](../sad.md)

> Adding word-count or reliability columns — the report holds them and one note beside the table is enough.
>
> — `spec.md §3, non-goals, verbatim` · full text: [spec.md](../spec.md)

> **Hard rule:** Language — 100% of the caption and the notes in Ukrainian, like the rest of the README. Rendering — plain markdown with 0 HTML.
>
> — `spec.md §6, Language and Rendering, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-05 — domain invariant: short evidence is never stated as conclusive

> **Given** fewer than all human samples reach 150 words in the last run
> **When** the text author reads the eval table
> **Then** a note beside the table states how many human samples reach 150 words out of how many, says the result for human texts is inconclusive, and does not present the table as proof that the detector never accuses a person
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-05b — edge: all human samples long enough

> **Given** every human sample reaches 150 words in the last run
> **When** the text author reads the eval table
> **Then** the note beside the table still states how many human samples reach 150 words out of how many, and no longer says the result for human texts is inconclusive
>
> — `spec.md §5, AC-05b, verbatim` · full text: [spec.md](../spec.md)

### AC-06 — domain invariant: the index is not proof

> **Given** a text author sees an index in the eval table
> **When** the text author reads the text around the table
> **Then** the README states that the index is a heuristic of signs of AI writing and not proof of authorship, by pointing to its existing section on the honest limit
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-10 — happy path

> **Given** the plugin author refreshed the table from a run on one detector copy
> **When** the text author reads the caption of the eval table
> **Then** the caption names the plugin whose detector copy was measured and the date of the run, the calendar date on which the plugin author ran the eval (the report prints none); plugin and date identify the run to the day
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Find the README's existing section on the honest limit («Чесна межа») and its anchor; do not edit that section.
- [ ] Under the table in `README.md`, write the caption: the plugin copy measured (`ukr-text-guard`) and the run date from T1.
- [ ] Read the report's line `human samples with 150 words or more: N of M` and write the evidence note from it: «N з M людських зразків мають 150 слів і більше». If N < M, say the result for human texts is inconclusive and the table is not proof the detector never accuses a person; if N = M, keep the count and drop the word inconclusive.
- [ ] Add one sentence near the table that the index is a heuristic of signs of AI writing, not proof of authorship, linking to the «Чесна межа» section.
- [ ] Touch no other README text; no HTML, no extra columns, no drift or hidden-character notes.

## Edge cases

| Case | Behaviour |
|---|---|
| Report line says 0 of N human samples reach 150 words | Note says «0 з N» and inconclusive |
| N = M (all human samples long enough) | Note keeps the count, no «inconclusive» |
| The honest-limit section was renamed | Follow its current heading; the link must resolve on the repository host page |
| Run date unclear (run on one day, edited on another) | Use the day the eval was run (T1), not the edit day |

## Definition of Done

- [ ] The caption names the plugin copy and the run date from T1, in Ukrainian.
- [ ] The evidence note states the count N of M taken from the report and the wording matches N < M or N = M.
- [ ] The text near the table says the index is not proof and links to «Чесна межа»; the link opens that section.
- [ ] every Hard Rule inlined above still holds
- [ ] README renders as plain markdown with 0 HTML
