---
id: T1
title: "Create the sources register skeleton"
layer: "docs"
deps: []
blocks: ["T2"]
acs: ["AC-02", "AC-08"]
files_hint: ["evals/samples/SOURCES.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"   # measured 42 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T1 — Create the sources register skeleton

## Place in the sequence

- **Blocked by:** — · **Blocks:** T2 — Select candidates and register the first batch · **Wave:** 1, no predecessor.
- **Lane:** starts the lane on `evals/samples/SOURCES.md` shared with T2 and T3 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** each human sample to have an author, genre, source, basis for publication, date of writing with its evidence, fragment borders and a log of changes to the text in the sources register
> **So that** I can later answer why the text counts as human and why it may sit in a public repository.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task fixes the shape of the register (fields, selection rule, change log, refusals section) so T2 and T3 only fill it in.

## Inlined context

> The register is a markdown file beside the samples, `evals/samples/SOURCES.md`: a non-`.txt` file the eval ignores, human-readable on review. Chosen over a JSON file because change logs and Ukrainian quotations must read as text.
>
> — `adr/0001, Decision outcome, abridged` · full text: [adr/0001](../adr/0001-keep-sources-register-as-markdown-beside-samples.md)

> **Selection rule:** the fragment runs from the start of the work or section to the first paragraph end after 150 words; length is measured with the analyzer's own `words()` function without calling `analyze()`; the only allowed text changes are the fragment cut, removed invisible characters and neutral replacement of personal details, each logged.
>
> — `sad.md §4, strategic choice 3, abridged` · full text: [sad.md](../sad.md)

> **Provenance fields:** author, genre (one of the four glossary genres), source, basis, date with evidence reference, fragment borders and blind word count, change log. ID: the sample name stem `human-<author>-<work>` is the key and the register section carries the same stem.
>
> — `sad.md §8, Provenance and ID strategy rows, abridged` · full text: [sad.md](../sad.md)

> **Defaults to write into the preamble:** (OQ-1) evidence of the date of writing for an own text: any dated original the plugin author can point to, recorded as a reference. (OQ-2) edition: the original public-domain text, never a modern edition with editorial rights; the version of a law in force before 2023.
>
> — `spec.md §8, OQ-1 and OQ-2, abridged` · full text: [spec.md](../spec.md)

> **Four genres:** business letters and mail; articles and blogs; technical and legal documents; fiction and informal style.
>
> — `CONTEXT.md, Glossary «Covered genre», abridged` · full text: [CONTEXT.md](../CONTEXT.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-02 (US-02) — happy path

> **Given** a human sample has been added to the check set
> **When** the plugin author reviews the sources register
> **Then** the register shows for that sample its author, genre, source, basis for publication, date of writing with a reference to its evidence, the borders of its fragment, and a log of every change made to the text
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-08 (US-02) — domain invariant: the text is not edited to suit the detector

> **Given** a candidate is prepared as a sample
> **When** the plugin author compares the sample with its source
> **Then** the only differences are the fragment cut, removed invisible characters, and personal details replaced by neutral words of the same kind, and each such change is recorded in the register
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Create `evals/samples/SOURCES.md` with a preamble: purpose, the selection rule above, the OQ-1 and OQ-2 defaults, the rule «a score is never a reason to change a candidate» (AC-06), and the list of permitted refusal and replacement reasons.
- [ ] Add an entry template with every field: author, genre, source, basis for publication, date of writing with evidence reference, fragment borders, blind word count, change log.
- [ ] Add a «Refusals» section with the template: candidate, reason (AC-05 / AC-06 / AC-07), date.
- [ ] Add the pre-ship review checklist: all fields filled; at least 3 authors, at least 1 another person; word counts 150 to 600; register commit precedes sample commit in `git log`; human files total ≤ 150 KB.

## Edge cases

| Case | Behaviour |
|---|---|
| Register picked up by the eval | `SOURCES.md` is not `.txt`, so the eval ignores it; one eval run must show no new unclassified item. |
| Register saved with BOM or CRLF | Fix to UTF-8 without BOM and LF (sad §8, File encoding). |

## Definition of Done

- [ ] `evals/samples/SOURCES.md` exists, UTF-8 without BOM, LF line ends.
- [ ] `bash evals/run.sh` prints no unclassified item caused by the register.
- [ ] Every field of AC-02 and the change-log rule of AC-08 appear in the entry template.
- [ ] Every Hard Rule inlined above still holds (no code changed).
