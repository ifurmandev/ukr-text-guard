---
id: T6
title: "Add the CLI entry point, detector copy lookup and exit code"
layer: "ports"
deps: ["T5"]
blocks: ["T7", "T8"]
acs: ["AC-11", "AC-16", "AC-18"]
files_hint: ["evals/run_eval.py", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T6 — Add the CLI entry point, detector copy lookup and exit code

## Place in the sequence

- **Blocked by:** T5 — Build the report, the evidence summary and the outcome decision · **Blocks:** T7 — Make `run.sh` a thin delegate, T8 — Prove independence and repeatability on the real analyzer · **Wave:** 4, the last piece of `run_eval.py`.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T1, T2, T3, T4, T5, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** to run the same set against each plugin's detector copy
> **So that** I can rely on the result after the copies are synchronised.
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task delivers the command line: choosing the plugin, finding its detector copy, printing the report and ending with exit code 0 or 1.

## Inlined context

> **Commands:** `python evals/run_eval.py [--plugin NAME] [--root DIR]`. Options: `--plugin NAME` default `ukr-text-guard`, allowed `ukr-text-guard`, `ukr-text-detector`, `ukr-text-editor`, one copy per run · `--root DIR` default the repo root derived from the script's own location, a test seam · `-h`, `--help` prints usage and exits 0. No other options: no order flag, no `--json`, no band flags. An invalid command line (unknown option, missing value) prints usage and exits 1, not 2, so only 0 and 1 exist.
>
> — `contracts/cli.md §1–§2, abridged` · full text: [cli.md](../contracts/cli.md)

> **Exit codes:** `0` nothing failed (notes and warnings may be present) · `1` anything else: analyzer failure, false alarm, miss, unclassified item, bad known-gap entry, missing category, missing detector copy, invalid command line, unhandled runner error (printed as `error eval.runner_error` followed by `result: failed`). Only 0 and 1 are used.
>
> — `contracts/cli.md §5, abridged` · full text: [cli.md](../contracts/cli.md)

> **Decision (ADR-0002):** exit code only — 0 on success, 1 on any failure; a failure of the runner itself (an unhandled exception) is caught at the top level and also exits 1, so a crash can never look like a pass.
>
> — `adr/0002, Decision outcome, abridged` · full text: [adr/](../adr/0002-signal-the-outcome-by-exit-code-only.md)

> **Flow: critical flow 1.** Resolve the detector copy of the chosen plugin. If that plugin has no detector copy → report that no copy exists and exit 1. Otherwise run the check, print the report, exit 0 if nothing failed, otherwise exit 1. Unhandled error inside the service → print `error eval.runner_error: …` and `result: failed`, exit 1.
>
> — `sad.md §6, «Critical flow 1» and «Flow: summarise the evidence and signal the outcome», abridged` · full text: [sad.md](../sad.md)

> **Correction to the contract (checked on disk, 2026-10-03):** `cli.md §3` gives the detector path as `plugins/<NAME>/skills/ukr-text-guard/scripts/analyze.py`, but the skill folder carries the plugin's own name. The real paths are `plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py`, `plugins/ukr-text-detector/skills/ukr-text-detector/scripts/analyze.py` and `plugins/ukr-text-editor/skills/ukr-text-editor/scripts/analyze.py`. Use `plugins/<NAME>/skills/<NAME>/scripts/analyze.py`; if the file is absent the copy does not exist (AC-18). Resolved in the review fix pass (2026-10-03): `cli.md` now names the real path.
>
> — `plugins/*/skills/*/scripts/, directory listing, observed` · full text: [cli.md](../contracts/cli.md)

> **Hard rule (Portability and Encoding):** the runner's own stdout is reconfigured to UTF-8 with `errors="replace"`; paths via `pathlib`.
>
> — `sad.md §8, Encoding and Portability, abridged` · full text: [sad.md](../sad.md)

Use `argparse` with its exit code 2 replaced by 1 (override `error()` or catch `SystemExit`). The duration printed in the report is measured here around `run_check` from T5. Failure kind: `eval.missing_detector_copy` and `eval.runner_error` ([cli.md](../contracts/cli.md) §6).

**Fallback:** insufficient or contradicted by the code → read [cli.md](../contracts/cli.md), [sad.md](../sad.md) §6, §8 and [adr/0002](../adr/0002-signal-the-outcome-by-exit-code-only.md) in full. Do not guess.

## Data delta

No DB changes.

## API contract

- Command: `python evals/run_eval.py [--plugin NAME] [--root DIR]` · exit `0` or `1` only.
- Missing copy line: `error eval.missing_detector_copy: no detector copy exists for plugin NAME`, then `result: failed`.

— `contracts/cli.md §1, §2, §5, §7, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-11 — cross-context

> **Given** each of the three text plugins (ukr-text-guard, ukr-text-detector, ukr-text-editor) carries its own detector copy
> **When** the plugin author runs the check against one chosen plugin's copy, or names none
> **Then** the report names the plugin whose copy was used (ukr-text-guard when none is named), the results come only from that copy, and a failing copy fails only its own run
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

### AC-16 — domain invariant: the outcome is usable without reading the report

> **Given** any run of the check
> **When** the run ends
> **Then** its outcome, success or failure, can be acted on automatically by the next step without reading the report
>
> — `spec.md §5, AC-16, verbatim` · full text: [spec.md](../spec.md)

### AC-18 — error

> **Given** the plugin author names a plugin that has no detector copy
> **When** the plugin author runs the check
> **Then** the report says that no detector copy exists for that plugin, and the run is reported as failed
>
> — `spec.md §5, AC-18, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `resolve_detector(root, plugin)` returning the path of `plugins/<plugin>/skills/<plugin>/scripts/analyze.py` or `None`, in `evals/run_eval.py`.
- [ ] Add `main(argv)` with `--plugin`, `--root`, `--help`; invalid command line prints usage and returns 1.
- [ ] Reconfigure stdout to UTF-8 with `errors="replace"`, print the report, return 0 or 1; wrap the whole run so any unhandled exception prints `error eval.runner_error: runner error: …` and `result: failed`, and returns 1.
- [ ] `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`.
- [ ] Tests in `evals/tests/test_run_eval.py` in a temporary repo root with a fake analyzer: default plugin named in the header, `--plugin` choosing another copy, missing copy, bad option, forced exception, exit codes 0 and 1.

## Edge cases

| Case | Behaviour |
|---|---|
| `--plugin ukr-text-unknown` | `eval.missing_detector_copy`, `result: failed`, exit 1 |
| No `--plugin` | header names `ukr-text-guard` |
| `--plugin` without a value, or `--bogus` | usage printed, exit 1 (not 2) |
| `--help` | usage printed, exit 0 |
| Exception inside the run | `error eval.runner_error` line and `result: failed`, exit 1, never exit 0 |
| One copy fails, another passes | each run's code reflects only its own copy |
| `--root` pointing to a folder without `plugins/` | treated as a missing detector copy |

## Definition of Done

- [ ] Tests for exit codes 0 and 1, the missing copy, the bad option and the forced exception pass.
- [ ] `python evals/run_eval.py --help` exits 0; no path through `main` returns a code other than 0 or 1.
- [ ] Running with the real repo root and no arguments reaches the real `ukr-text-guard` copy and prints a report.
- [ ] Every Hard Rule inlined above still holds.
