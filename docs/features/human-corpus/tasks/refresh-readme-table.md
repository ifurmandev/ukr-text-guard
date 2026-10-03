---
id: T5
title: "Refresh the README table and caption"
layer: "docs"
deps: ["T4"]
blocks: []
acs: ["AC-09", "AC-10", "AC-11", "AC-12"]
files_hint: ["README.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"   # measured 56 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T5 — Refresh the README table and caption

## Place in the sequence

- **Blocked by:** T4 — Run the check and verify the verdict · **Blocks:** — · **Wave:** 5, after the report.
- **Lane:** own lane; parallel with T6 (different files).

## Why (user story)

> **As a** plugin author
> **I want** the README table and caption to show the new set and the genres covered or not covered
> **So that** the published figures match the latest report.
>
> — `spec.md §4, US-07, verbatim` · full text: [spec.md](../spec.md)

> **As a** text author
> **I want** to see in the README which genres and how many authors the measured quality rests on
> **So that** I do not read a result for classic or official texts as proof for my own kind of text.
>
> — `spec.md §4, US-08, verbatim` · full text: [spec.md](../spec.md)

This task copies the report into the README by hand and states what the figures cover and what they do not.

## Inlined context

> **Flow D:** refresh rows and counts from the report; drop the rows of the two removed samples; if the conclusion is inconclusive, say so in the note; for each genre, name it covered or not covered with the reason; state the author count and that the set holds classic, official and own texts only.
>
> — `sad.md §6, Flow D, abridged` · full text: [sad.md](../sad.md)

> **Current table (README «Перевірка»):** columns `Зразок | Категорія | Очікувана смуга | Відомий пропуск | Індекс | Результат`; rows `human-business-letter` and `human-story` (to be removed); caption «Усього N зразків: …», the run line «Таблиця: прогін `bash evals/run.sh` на копії детектора з плагіна `ukr-text-guard`, <date>», and the note «0 з 2 людських зразків мають 150 слів і більше…».
>
> — `README.md, section «Перевірка», abridged` · full text: [README.md](../../../../README.md)

> **Uncovered genres (risk):** no free source of modern business mail, blogs or informal fiction with a proven pre-AI date; the caption names each uncovered genre with the reason and never presents the result as proof for modern text. A formal text above 25 is recorded as a known limitation.
>
> — `sad.md §11, Risks rows 1–2, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** README text is Ukrainian; the table stays a manual refresh from the report; the eval, detector and bands are not changed.
>
> — `sad.md §2 Conventions and spec.md §3, abridged` · full text: [spec.md](../spec.md)

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

### AC-10 (US-07) — cross-context

> **Given** the check set has the new human samples
> **When** the plugin author refreshes the README table from the latest report
> **Then** every row, the sample counts and the count of human samples reaching 150 words match the report, and the caption names each covered genre and each genre that is not covered with the reason
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

### AC-11 (US-08) — happy path

> **Given** a text author opens the README after the refresh
> **When** the text author reads the eval table and its note
> **Then** the text author sees how many authors the human samples come from, which genres are covered, and a plain statement that the set holds classic, official and the plugin author's own texts and does not prove the detector safe for other kinds of modern text
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

### AC-12 (US-03) — error

> **Given** a human sample of fewer than 150 words is in the set
> **When** the plugin author runs the check
> **Then** the report marks the human conclusion as inconclusive and the README note says so, and the step is not reported as done
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Copy the report into `README.md`: rows for every human sample, counts, run date; keep the AI rows as in the report; remove the `human-business-letter` and `human-story` rows.
- [ ] Update the sentence with sample counts and the number of human samples with 150 words or more.
- [ ] Write the caption in Ukrainian: number of authors, each covered genre, each uncovered genre with its reason, and the plain statement that the set holds classic, official and the plugin author's own texts and does not prove the detector safe for other kinds of modern text.
- [ ] If the report marks the human conclusion inconclusive, say so in the note; if a human sample is a false alarm, show it with the result from the report.
- [ ] Compare every row and count against `docs/features/human-corpus/eval-report.txt` once more.

## Edge cases

| Case | Behaviour |
|---|---|
| False alarm in the report | The row shows the failed result; the caption names it as a known limitation; it is not softened. |
| Human conclusion inconclusive | The note says so (AC-12). |
| A genre without a 150-word sample | The caption names it as not covered, with the reason (AC-10). |

## Definition of Done

- [ ] Every README row and count equals the report in `eval-report.txt`.
- [ ] Neither the table nor the text lists the two removed samples.
- [ ] The caption names the author count, covered and uncovered genres with reasons, and the plain statement.
- [ ] Every Hard Rule inlined above still holds.
