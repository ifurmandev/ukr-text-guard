---
status: Accepted
owner: "Ihor Furman"
reviewers: ["Tech Lead"]
updated_at: "2026-10-03"
feature_size: "S"
ticket: "roadmap step 1 — ukr-text-eval"
---

# 0002 — Signal the outcome by exit code only

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Ihor Furman (plugin author) with the architect, during the design walk

## Context

AC-16 requires that the outcome of every run, success or failure, can be acted on automatically by the next step without reading the report. The next steps are the copy-sync check (roadmap step 4) and later the quiet hook (step 5). Step 5 is also meant to take its thresholds from the eval results (roadmap D3), so structured per-sample numbers may become useful. The question is whether the runner should offer a second, machine-readable output now.

## Decision drivers

- AC-16: outcome usable without reading the report.
- AC-19: warnings, drift notes and the inconclusive mark never change the outcome, so the outcome is a single success-or-failure signal.
- The feature is size S; the spec lists 19 acceptance criteria and none describes a structured output.
- A second output format must be kept in step with the text report and covered by tests, and consumers would start to depend on its schema.

## Considered options

1. **Exit code only** — 0 on success, 1 on any failure; the printed report is for people.
2. **Exit code plus a `--json` flag** — the runner also prints per-sample results (name, category, index, word count, reliability, verdict) as JSON.

## Decision outcome

**Chosen:** Option 1. The exit code is exactly what AC-16 asks for. If step 5 needs numbers, adding `--json` then is an additive change with its own acceptance criteria; doing it now would widen a size-S step and freeze a schema nobody has asked for yet. A failure of the runner itself (an unhandled exception) is caught at the top level and also exits 1, so a crash can never look like a pass.

## Consequences

**Positive**
- One output format to maintain and test; the contract for later steps is two values.
- Fail-closed: every path that is not an explicit success ends in a non-zero code.

**Negative**
- A consumer that needs the numbers must parse the text report or wait for a `--json` flag. Roadmap step 5 is the likely first consumer.
- The code cannot tell «the detector failed» from «the runner or its inputs are broken»; both are 1, and the report says which.

**Neutral**
- Adding `--json` later does not change the exit-code contract.

## Links

- Spec: [[../spec.md]] (AC-16, AC-19)
- SAD: [[../sad.md]] §4, §8
- Related ADR: [[0001-keep-known-gaps-in-a-plain-list-file]]
