---
id: T3
title: "Add the sample files and remove the two short ones"
layer: "docs"
deps: ["T2"]
blocks: ["T4"]
acs: ["AC-02", "AC-08", "AC-09"]
files_hint: ["evals/samples/human-*.txt", "evals/samples/human-business-letter.txt", "evals/samples/human-story.txt", "evals/samples/SOURCES.md"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"   # measured 50 inlined lines
status: "done"
---

<!-- Governing rule: inline the slice the task needs, name where it came from, keep the link as fallback.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous, or
contradicts the code in front of you, open the named file for the full text. Do not invent the missing part. -->

# T3 — Add the sample files and remove the two short ones

## Place in the sequence

- **Blocked by:** T2 — Select candidates and register the first batch · **Blocks:** T4 — Run the check and verify the verdict · **Wave:** 3, after the register commit.
- **Lane:** shares `evals/samples/SOURCES.md` with T1 and T2 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** each human sample to have an author, genre, source, basis for publication, date of writing with its evidence, fragment borders and a log of changes to the text in the sources register
> **So that** I can later answer why the text counts as human and why it may sit in a public repository.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

> **As a** plugin author
> **I want** the two short human samples replaced by longer texts
> **So that** the condition «every human sample reaches 150 words» can hold.
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task turns the registered fragments into files, logs every permitted change, and removes the two short samples.

## Inlined context

> **Permitted differences from the source:** the fragment cut, removed invisible characters, and personal details replaced by neutral words of the same kind; each change is logged. Anything else is restored to the source text.
>
> — `sad.md §6, Flow A, abridged` · full text: [sad.md](../sad.md)

> **File rules:** UTF-8 without BOM, LF line ends, no invisible characters (so the eval raises no «hidden characters» note); name `human-<author>-<work>.txt`; the eval classifies `*.txt` by the `human-` / `ai-` prefix and fails the run on a plain-text file with another prefix.
>
> — `sad.md §2 and §8, Conventions and File encoding, abridged` · full text: [sad.md](../sad.md)

> **Removal:** `human-business-letter.txt` (67 words) and `human-story.txt` (101 words) are removed because their length is below 150 words, never because of their indexes (AC-06, AC-09).
>
> — `sad.md §5, Internal decomposition, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** the register commit must precede this commit in `git log`; a later addition's register entry precedes its file.
>
> — `adr/0002, Decision outcome, abridged` · full text: [adr/0002](../adr/0002-commit-register-before-sample-files.md)

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

### AC-09 (US-06) — cross-context

> **Given** the two short human samples are replaced by longer texts
> **When** the plugin author runs the check and refreshes the README table
> **Then** neither the report nor the README table lists the old samples, and the changelog states that their earlier indexes are no longer part of the baseline
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Create each `evals/samples/human-<author>-<work>.txt` by copying the fragment between the registered borders.
- [ ] List every difference from the source; keep only the permitted ones; log each in that sample's change log in `evals/samples/SOURCES.md` (or write «none»).
- [ ] Check encoding: no BOM, LF, no zero-width or other invisible characters.
- [ ] Remove `evals/samples/human-business-letter.txt` and `evals/samples/human-story.txt` with `git rm`.
- [ ] Check the summed size of the human files is ≤ 150 KB.
- [ ] Commit (`feat(human-corpus): add human samples, remove two short ones`).

## Edge cases

| Case | Behaviour |
|---|---|
| A permitted-looking change not in the log | Not allowed: log it or restore the source text. |
| Urge to improve a sentence after seeing a report | Not allowed (AC-06, AC-08); the sample stays as registered. |
| File with another prefix or extension | The eval fails the run as unclassified; rename to `human-*.txt`. |
| Total over 150 KB | Refuse the largest candidate for a length reason and record it; do not trim by hand. |

## Definition of Done

- [ ] Each sample equals its source apart from logged changes.
- [ ] Each human file is UTF-8 without BOM and has no invisible characters.
- [ ] The two short files are gone; the register commit precedes this commit in `git log`.
- [ ] Summed size of human files ≤ 150 KB.
- [ ] Every Hard Rule inlined above still holds.
