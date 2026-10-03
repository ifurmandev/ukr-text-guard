---
id: T6
title: "Write the changelog note on the removed baseline"
layer: "docs"
deps: ["T4"]
blocks: []
acs: ["AC-09"]
files_hint: ["docs/features/human-corpus/changelog.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"   # measured 30 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T6 — Write the changelog note on the removed baseline

## Place in the sequence

- **Blocked by:** T4 — Run the check and verify the verdict · **Blocks:** — · **Wave:** 5, after the report.
- **Lane:** own lane; parallel with T5 (different files).

## Why (user story)

> **As a** plugin author
> **I want** the two short human samples replaced by longer texts
> **So that** the condition «every human sample reaches 150 words» can hold.
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task records that the two removed samples and their indexes are no longer part of the baseline, plus the final set.

## Inlined context

> **Changelog statement:** the changelog states that the earlier indexes of the two removed samples (`human-business-letter`, index 0, 67 words; `human-story`, index 7, 101 words) are no longer part of the baseline.
>
> — `sad.md §5, changelog (at ship) row, abridged` · full text: [sad.md](../sad.md)

> **Format of a feature changelog:** follow the previous step's file for tone and length.
>
> — `docs/features/readme-eval-table/changelog.md, abridged` · full text: [changelog.md](../../readme-eval-table/changelog.md)

> **Boundary:** `ship` later expands this file with the PR link; this task only fixes the facts it must keep.
>
> — `tasks breakdown, this task, abridged`

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-09 (US-06) — cross-context

> **Given** the two short human samples are replaced by longer texts
> **When** the plugin author runs the check and refreshes the README table
> **Then** neither the report nor the README table lists the old samples, and the changelog states that their earlier indexes are no longer part of the baseline
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Create `docs/features/human-corpus/changelog.md` following the layout of `docs/features/readme-eval-table/changelog.md`.
- [ ] State the new set: authors, sample files, word counts and indexes from `eval-report.txt`.
- [ ] State that the earlier indexes of the two removed samples are no longer part of the baseline, and that the reason for removal was length.
- [ ] List known limitations observed: false alarms and uncovered genres, as in the README caption.

## Edge cases

| Case | Behaviour |
|---|---|
| A false alarm in the report | Listed as a known limitation; not omitted. |
| Earlier indexes quoted | Quoted only to mark them as out of the baseline; never as a reason for the removal. |

## Definition of Done

- [ ] `changelog.md` exists and states that the two earlier indexes are no longer part of the baseline.
- [ ] Figures equal `eval-report.txt`.
- [ ] Every Hard Rule inlined above still holds.
