---
id: T2
title: "Select candidates and register the first batch"
layer: "docs"
deps: ["T1"]
blocks: ["T3"]
acs: ["AC-01", "AC-05", "AC-06", "AC-07"]
files_hint: ["evals/samples/SOURCES.md"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"   # measured 62 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T2 — Select candidates and register the first batch

## Place in the sequence

- **Blocked by:** T1 — Create the sources register skeleton · **Blocks:** T3 — Add the sample files and remove the two short ones · **Wave:** 2, needs the entry template.
- **Lane:** shares `evals/samples/SOURCES.md` with T1 and T3 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** every candidate and the borders of its fragment recorded before the analyzer is first run on the text
> **So that** the choice of texts cannot follow the scores.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

> **As a** plugin author
> **I want** a candidate without a nameable basis for publication refused and the refusal recorded
> **So that** the public repository holds no text it has no right to hold.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task chooses candidates mechanically, counts words blind, records every refusal, and commits the register before any sample file exists.

## Inlined context

> **Register first, samples second:** the whole first batch of candidates, with their fragment borders, is committed to the register in one commit before the analyzer is run on any of them and before any sample file is committed. A later addition repeats the pattern: its register entry first, its file second.
>
> — `sad.md §4, strategic choice 1, abridged` · full text: [sad.md](../sad.md)

> The commit order is the evidence. Length is measured with the analyzer's word counter only (no `analyze()` call).
>
> — `adr/0002, Decision outcome, abridged` · full text: [adr/0002](../adr/0002-commit-register-before-sample-files.md)

> **Refusal branch:** refusal reasons are the spec's: another person's modern text, a modern edition with editorial rights, or an own text that still holds third-party data (AC-05); a fragment below 150 or above 600 words under the selection rule (AC-06); a date of writing that is unknown or 2023 or later (AC-07).
>
> — `sad.md §6, Critical flow 1 prose, abridged` · full text: [sad.md](../sad.md)

> **Goal of the set:** human texts from at least three authors, one of them another person (neither the plugin author nor an official body); every sample 150 to 600 words by the analyzer's own count; human files total ≤ 150 KB.
>
> — `spec.md §1 and §6, abridged` · full text: [spec.md](../spec.md)

> **Hard rule:** no personal data or third-party content may remain; a text without a nameable basis for publication does not enter the repository.
>
> — `spec.md §6.1, Personal data touched, abridged` · full text: [spec.md](../spec.md)

> **Word counter:** `words(t)` in `plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py` (line 228); import and call only this function.
>
> — `analyze.py, def words, abridged`

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-01 (US-01) — happy path

> **Given** the plugin author has chosen candidates and fixed the selection rule that gives the borders of each fragment
> **When** the plugin author records them in the sources register before running the analyzer on any of them
> **Then** the register lists each candidate with its fragment borders, and each sample in the check set can be matched to an entry made earlier
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-05 (US-05) — authorization: no text enters without a nameable basis for publication

> **Given** a candidate is another person's modern text, a modern edition with editorial rights, or the plugin author's own text that still holds third-party personal data or confidential content after personal details are replaced
> **When** the plugin author considers adding it to the check set
> **Then** the candidate is not added, and the register records the refusal with the reason
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-06 (US-01) — domain invariant: a score is never a reason to change the set

> **Given** the analyzer has been run on a text and gave an index the plugin author did not expect
> **When** the plugin author considers replacing the text, dropping it or moving its fragment borders
> **Then** the sample stays exactly as recorded, and the register accepts a refusal or a replacement only for provenance, basis for publication, a length below 150 words or above 600 words under the selection rule, or a defect of the file, never for the index
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-07 (US-02) — domain invariant: only texts written before 2023 count as human

> **Given** a candidate whose date of writing is unknown or falls in 2023 or later
> **When** the plugin author considers adding it as a human sample
> **Then** the candidate is refused as human, and the register records the refusal with the reason
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Pick candidates by hand from public-domain classics, official documents in the version in force before 2023, and own dated pre-2023 texts: at least 3 authors, at least 1 another person.
- [ ] For each candidate apply the selection rule to get the fragment borders; count words with `words()` only, never `analyze()` or `run_eval.py`.
- [ ] Fill one register section per acceptable candidate in `evals/samples/SOURCES.md`: all fields, evidence reference, borders, blind word count, empty change log.
- [ ] Fill the Refusals section for every rejected candidate with its reason (AC-05, AC-06 length, AC-07).
- [ ] Commit the register only (`docs(human-corpus): register first batch of candidates`) before any `human-*.txt` file is added, and push it before the sample commit.

## Edge cases

| Case | Behaviour |
|---|---|
| Fragment over 600 words under the rule | Refuse the candidate and record the reason (AC-06); do not shorten it by hand. |
| Fragment below 150 words | Refuse and record; choose the next candidate under the same rule. |
| Own text with names or contacts | Plan neutral replacement and log it in T3, or refuse (AC-05). |
| Date unknown or 2023 and later | Refuse as human (AC-07). |
| Fewer than 3 acceptable authors | Keep selecting; T3 does not start. |

## Definition of Done

- [ ] Register has at least 3 authors, at least 1 another person, every field filled for each.
- [ ] Every candidate has borders and a blind word count of 150 to 600.
- [ ] Every refused candidate has its reason.
- [ ] The register commit exists in `git log` and contains no `human-*.txt` file.
- [ ] `analyze()` and `run_eval.py` were never run on a candidate (state it in the commit body).
