---
status: Accepted
owner: "Ihor Furman"
reviewers: ["Tech Lead"]
updated_at: "2026-10-03"
feature_size: "S"
ticket: "N/A"
---

# 0001 — Keep the sources register as a markdown file beside the samples

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Ihor Furman, Claude (design stage, easy depth)

## Context

Every human sample needs a record of its author, genre, source, basis for publication, date of writing with its evidence, fragment borders and a log of changes, and every refused candidate needs its reason (spec AC-02, AC-05). The CONTEXT glossary puts this register in the sample folder. The eval classifies only `*.txt` files and ignores every other file in that folder (`evals/run_eval.py:56-71`), so the register's file type decides whether the eval leaves it alone and who or what can read it later.

## Decision drivers

- A register in `.txt` form would be classified as unclassified and fail the run (`evals/run_eval.py:56-71`).
- Register completeness is 100% at review (spec §6) and is judged by a person with a checklist today.
- The register holds Ukrainian quotations, long refusal reasons and a change log, which a person must read on review.
- Whether the eval should later check the register is an open question (spec §8 OQ-3); the format should not make the answer expensive.

## Considered options

1. **Markdown file `evals/samples/SOURCES.md`** — a selection-rule preamble and one section per candidate with a field list, plus a refusals section.
2. **Structured file `evals/samples/sources.json`** — an array of objects with the same fields.

## Decision outcome

**Chosen:** Option 1, the markdown file. It reads as text on review, holds Ukrainian prose and long reasons without escaping, and the eval already ignores it. The cost of option 2, unreadable change logs and a file that one stray comma breaks, outweighs the gain of an eval check that is not in scope for this step.

## Consequences

**Positive**
- Reviewable in a pull request as plain text; no new code.
- The eval needs no change: a non-`.txt` file is listed under «ignored» in the report.

**Negative**
- A machine cannot read the register without a parser, so the completeness check stays a manual checklist.

**Neutral**
- If OQ-3 later says the eval should check the register, either a small parser for the fixed field list is added or the entries migrate to a structured file; both are bounded jobs, the migration touching every entry.

## Links

- Spec: [[../spec.md]] (AC-02, AC-05, §6 register completeness, §8 OQ-3)
- SAD: [[../sad.md]] §4
- Related ADR: [[0002-commit-register-before-sample-files]]
