---
id: T9
title: "Run the acceptance checks: eval parity on all three analyzer copies, plugin folders unchanged, NFRs"
layer: "tests"
deps: ["T1", "T4", "T7", "T8"]
blocks: []
acs: ["AC-13", "AC-14"]
files_hint: ["docs/features/shared-detector/acceptance.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T9 — Run the acceptance checks: eval parity on all three analyzer copies, plugin folders unchanged, NFRs

## Place in the sequence

- **Blocked by:** T1 — seed shared/, T4 — sync, T7 — run.sh, T8 — docs · **Blocks:** — · **Wave:** 6, the last: a one-off verification of the finished step.
- **Lane:** own lane (writes only its record file).

## Why (user story)

> **As a** text author
> **I want** every plugin to keep the same files on the same paths and the detector to give the same results
> **So that** my installed plugin works as before.
>
> — `spec.md §4, US-07, verbatim` · full text: [spec.md](../spec.md)

This task proves US-07 and the spec §6 targets on the real repository, and records the result.

## Inlined context

> AC-13 and AC-14 are non-runtime: AC-13 is a one-off acceptance run of the eval on each analyzer copy, compared with the committed table; AC-14 is a one-off comparison of the plugin folders before and after the step (`git diff --stat`).
>
> — `sad.md §6, coverage table (AC-13, AC-14), abridged` · full text: [sad.md](../sad.md)

> NFR targets: duration of `check` and of `sync` ≤ 2 s for 5 shared files in 3 plugins (timed standalone run); idempotence — the second sync in a row rewrites 0 files and the first sync on the current files rewrites 0 files; unchanged eval — 0 changed lines in the eval runner and its unit tests, 74 of 74 existing unit tests pass; completeness — each of the 4 divergence kinds is caught by at least 1 automated test; environment — works with each of the 3 interpreters (`python3`, `python`, `py`) present on the machine, 0 imports outside the standard library.
>
> — `spec.md §6, NFR table, abridged` · full text: [spec.md](../spec.md)

> The eval's report is classified per sample by the `human-` / `ai-` prefix; `bash evals/run.sh` runs the guard copy by default and `--plugin <name>` selects another plugin's copy of `analyze.py`. The committed table is in the README (3 October 2026, 11 of 11 samples on the guard copy).
>
> — `docs/architecture-map.md (Evals row) + README.md eval table, abridged` · full text: [README.md](../../../../README.md)

> **Hard rule:** no file is added to, removed from or moved in any plugin folder; 0 changed lines in `evals/run_eval.py` and `evals/tests/`. This task records results, it changes no code.
>
> — `spec.md §5 AC-14 + §6 (Unchanged eval), abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md), [sad.md](../sad.md), [README.md](../../../../README.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-13 — cross-context

> **Given** the sync has run and its result is committed
> **When** the plugin author runs the eval on the analyzer of each of the three plugins in turn
> **Then** every sample gets, on all three, the same index and the same row result as in the eval table committed in the README before this step
>
> — `spec.md §5, AC-13, verbatim` · full text: [spec.md](../spec.md)

### AC-14 — cross-context

> **Given** the sync has run and its result is committed
> **When** the plugin author compares the folder of each of the three plugins in the repository before and after the step
> **Then** every file that the plugin's skill description tells Claude to read is present on the same path as before the step, and no file was added, removed or moved
>
> — `spec.md §5, AC-14, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Run `sync` on the real repository: expect `all copies are up to date`, 0 rewritten; run it twice; run `check`: `checked 12 files in 3 plugins`, exit 0.
- [ ] Run `bash evals/run.sh` for each of `ukr-text-guard`, `ukr-text-detector`, `ukr-text-editor` (via `--plugin`); compare every sample's index and row result with the README table.
- [ ] `git diff --stat <commit before the step>..HEAD -- plugins` shows no added, removed or moved file; check each plugin's SKILL.md read-list against the folder.
- [ ] `git diff --stat` for `evals/run_eval.py` and `evals/tests/` is empty; `python -m unittest discover evals/tests` → 74 of 74; `python -m unittest discover tools/tests` passes.
- [ ] Time `check` and `sync` (≤ 2 s) with each present interpreter.
- [ ] Write the outcomes, with commands and outputs, to `docs/features/shared-detector/acceptance.md`.

## Edge cases

| Case | Behaviour |
|---|---|
| An index differs on one analyzer copy | Not expected (copies were byte-identical on 2026-10-04); report which copy and sample, do not edit the detector |
| `py` or `python3` absent on the machine | that interpreter is marked «not present», not a failure (spec §6 Environment) |
| A plugin does not accept `--plugin` | read `evals/run_eval.py` for the real flag; do not change the runner |

## Definition of Done

- [ ] acceptance record lists AC-13 per plugin and AC-14 with the `git diff --stat` output
- [ ] NFRs of spec §6 are each marked met, with the measurement
- [ ] 74 of 74 existing unit tests and all new tests pass
- [ ] every Hard Rule inlined above still holds
