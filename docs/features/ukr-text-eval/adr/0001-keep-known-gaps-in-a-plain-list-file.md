---
status: Accepted
owner: "Ihor Furman"
reviewers: ["Tech Lead"]
updated_at: "2026-10-03"
feature_size: "S"
ticket: "roadmap step 1 — ukr-text-eval"
---

# 0001 — Keep known-gaps in a plain list file

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Ihor Furman (plugin author) with the architect, during the design walk

## Context

The check must excuse AI samples that the detector is known to miss (known-gap) without letting the excuse hide a real regression (spec §6.1 abuse cases). The spec fixes the behaviour: only an explicit entry by the plugin author excuses a sample (AC-07), a known-gap on a human sample is an error (AC-13), and a known-gap naming a sample that does not exist is an error (AC-14). The category of a sample comes from its file name prefix `human-` or `ai-` (AC-12), and the bands are fixed before the run (spec §1). The next roadmap steps (README table, broader human set, copy sync, quiet hook) all read whatever format is chosen here.

## Decision drivers

- AC-14: a flag must be able to name a sample that does not exist, so the flag cannot live inside the sample's own file name.
- AC-07 and spec §6.1: every excused sample must be visible in the report and in review.
- Spec §6 NFR «Cost of adding a sample of a known category»: 0 edits to expected bands — adding a sample must not touch the band definition.
- AC-12 and US-07: a file without a `human-` or `ai-` prefix is reported as unclassified, so the prefix stays the single source of a sample's category.
- Roadmap steps 2–5 read this format, so it should stay easy to read by hand and by script.

## Considered options

1. **A plain list file `evals/known-gaps.txt` with an optional reason after `#`** — one sample name per line, comment lines and blank lines ignored, the reason printed in the report when present.
2. **The same list file with a mandatory reason** — a line without a reason is a run error.
3. **A JSON manifest `evals/expected.json`** — one record per sample with `category`, `known_gap` and `reason`.

## Decision outcome

**Chosen:** Option 1. Category comes from the file name prefix, the bands are named constants in `evals/run_eval.py`, and known-gap is an explicit line in `evals/known-gaps.txt`. A mandatory reason (option 2) would add an error class that none of the 19 acceptance criteria describes, and a manifest (option 3) would create a second source of truth for the category that can drift from the file name and would make every new sample an edit in two places.

## Consequences

**Positive**
- Adding a sample is one new file, and at most one line in the list; the band constants are untouched (NFR «0 edits to expected bands»).
- A relabelled failing sample is a one-line diff in `known-gaps.txt`, visible in review and printed in the report every run (AC-07).
- Later steps read a format a person can edit without documentation.

**Negative**
- Nothing forces a reason: the discipline rests on code review, and a reason-less line is still accepted.
- No machine-readable manifest exists for step 2 to generate the README table from; that step reads the list and the constants.

**Neutral**
- Moving to a manifest later is possible and mechanical (the list is tiny), but the category rule in AC-12 would then need a new acceptance criterion.
- The first run flags one sample: `ai-prompted-human-style` (index 9). `ai-engineered-humanity` (index 29) already reaches the AI band, so it stays an ordinary AI sample (spec §1). Amended 2026-10-03 after review: the original text listed both samples.

## Links

- Spec: [[../spec.md]] (AC-07, AC-12, AC-13, AC-14, §6 NFR, §6.1)
- SAD: [[../sad.md]] §4, §5
- Related ADR: [[0002-signal-the-outcome-by-exit-code-only]]
