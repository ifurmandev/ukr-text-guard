---
id: T3
title: "Read and validate the known-gap list, seed it with the first entry"
layer: "infra"
deps: ["T2"]
blocks: ["T5"]
acs: ["AC-13", "AC-14"]
files_hint: ["evals/run_eval.py", "evals/known-gaps.txt", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T3 — Read and validate the known-gap list, seed it with the first entry

## Place in the sequence

- **Blocked by:** T2 — Discover and classify the items of the sample folder · **Blocks:** T5 — Build the report and the outcome · **Wave:** 2, needs the classified sample set to validate names against.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T1, T2, T4, T5, T6, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** bypass samples kept as known-gap, and a warning when one reaches the AI band
> **So that** I notice when a gap closes without a failing run.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task delivers the explicit, validated list that is the only way a sample gets the known-gap flag.

## Inlined context

> **Decision (ADR-0001):** known-gap is an explicit line in `evals/known-gaps.txt`: one sample name per line, comment lines and blank lines ignored, the reason after `#` printed in the report when present. Nothing forces a reason; a reason-less line is still accepted.
>
> — `adr/0001, Considered options 1 and Consequences, abridged` · full text: [adr/](../adr/0001-keep-known-gaps-in-a-plain-list-file.md)

> **Flow: validate and classify, known-gap step.** For each known-gap entry: names a sample that does not exist → record a bad-entry failure naming it · names a human sample → record a bad-entry failure and keep judging it as human · names an AI sample → set the known-gap flag on that sample.
>
> — `sad.md §6, «Flow: validate and classify the sample folder», abridged` · full text: [sad.md](../sad.md)

> **Inputs, Known-gap list:** `evals/known-gaps.txt` — one AI sample name (file name without `.txt`) per line, optional `# reason`. A name that does not exist, or names a human sample, is an error. A missing file is treated as an empty list (OQ-B).
>
> — `contracts/cli.md §3, Known-gap list, verbatim` · full text: [cli.md](../contracts/cli.md)

> **Flagged during `sequences`:** the first known-gap list holds only `ai-prompted-human-style` (index 9). `ai-engineered-humanity` (index 29) already reaches the AI band of 26, so it is an ordinary AI sample and not a known-gap. Spec §1 and ADR-0001 (Consequences) still say the first run flags both samples. The flows are unaffected, because a known-gap sample at 26 or above still gets the gap-may-be-closed warning.
>
> — `sad.md §6, «Flagged for spec and ADR-0001», verbatim` · full text: [sad.md](../sad.md)

Seed `evals/known-gaps.txt` with `ai-prompted-human-style` as the sad decides; the spec and ADR text are stale on this point (source disagreement noted in the epic). Failure kind: `eval.bad_known_gap` ([cli.md](../contracts/cli.md) §6). OQ-B (missing file = empty list) is a proposal in the contract; apply it as written.

**Fallback:** insufficient or contradicted by the code → read [adr/0001](../adr/0001-keep-known-gaps-in-a-plain-list-file.md), [sad.md](../sad.md) §6 and [cli.md](../contracts/cli.md) §3 in full. Do not guess.

## Data delta

No DB changes. The list is a text file, `evals/known-gaps.txt`.

## API contract

Internal — no API surface. File format: [cli.md](../contracts/cli.md) §3.

## Acceptance criteria

### AC-13 — domain invariant: known-gap applies only to AI samples

> **Given** the plugin author has put a known-gap flag on a human sample
> **When** the plugin author runs the check
> **Then** the report lists that flag as an error naming the sample, the sample is judged against the human band as usual, and the run is reported as failed
>
> — `spec.md §5, AC-13, verbatim` · full text: [spec.md](../spec.md)

### AC-14 — error

> **Given** a known-gap flag names a sample that does not exist
> **When** the plugin author runs the check
> **Then** the report lists the flag as an error naming it, and the run is reported as failed
>
> — `spec.md §5, AC-14, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `read_known_gaps(path)` in `evals/run_eval.py` returning ordered `(name, reason)` pairs; skip blank and `#` lines; a missing file gives an empty list.
- [ ] Add `apply_known_gaps(entries, classified)` returning the set of flagged AI names and the list of `eval.bad_known_gap` errors (missing name, human name).
- [ ] Create `evals/known-gaps.txt` with `ai-prompted-human-style  # imitates human writing, index 9 on the first run`.
- [ ] Tests in `evals/tests/test_run_eval.py` for flag on AI, on human, on a missing name, comments, blank lines and a missing file.

## Edge cases

| Case | Behaviour |
|---|---|
| Entry names a human sample | `eval.bad_known_gap`; the sample gets no flag and is judged as human |
| Entry names a missing sample | `eval.bad_known_gap` naming it |
| Entry without a reason | accepted, reason empty |
| Duplicate entry | one flag, no error |
| `known-gaps.txt` missing | empty list, no failure |
| Line with trailing spaces or CRLF | name is trimmed, matches normally |

## Definition of Done

- [ ] Unit tests for the three entry outcomes and the file-format cases pass.
- [ ] A flagged AI sample reaches `judge()` with `known_gap=True`; a bad entry never produces a flag.
- [ ] `evals/known-gaps.txt` exists with the seeded line.
