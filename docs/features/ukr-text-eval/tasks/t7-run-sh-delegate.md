---
id: T7
title: "Make run.sh a thin delegate that finds a working Python"
layer: "wiring"
deps: ["T6"]
blocks: ["T9"]
acs: ["AC-16"]
files_hint: ["evals/run.sh"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"
status: "done"
---

# T7 — Make run.sh a thin delegate that finds a working Python

## Place in the sequence

- **Blocked by:** T6 — CLI entry point, detector copy lookup and exit code · **Blocks:** T9 — Verify the first real run on both shells and update the docs · **Wave:** 5, runs in parallel with T8 (different files).
- **Lane:** own lane (`evals/run.sh` is touched by no other task).

## Why (user story)

> **As a** plugin author
> **I want** to run all samples against expected bands and get a pass/fail report
> **So that** I know whether the detector works.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task keeps the documented command `bash evals/run.sh` working on a machine where `python3` is a broken Store stub, and passes the runner's exit code through.

## Inlined context

> `evals/run.sh` stays as a thin delegate so the documented command `bash evals/run.sh` keeps working: it tries `python3`, `python` and `py`, checks that the candidate really starts, and hands over to the runner. Verdicts live only in `run_eval.py`.
>
> — `sad.md §5, abridged` · full text: [sad.md](../sad.md)

> **`run.sh`:** thin delegate. Probes `python3`, `python` and `py`, checks that the candidate really starts, passes every argument through unchanged. Adds no flags and no verdicts.
>
> — `contracts/cli.md §1, Commands, verbatim` · full text: [cli.md](../contracts/cli.md)

> **Risk:** `python3` on the author's Windows machine is a Microsoft Store stub, so the current `evals/run.sh` cannot run there. Mitigation: `run.sh` probes interpreters and verifies each one starts.
>
> — `sad.md §11, Risks, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** only exit codes 0 and 1 exist; the script's exit code is the runner's exit code, and when no working Python is found it exits 1 with a message (never 0).
>
> — `contracts/cli.md §5 and adr/0002, abridged` · full text: [cli.md](../contracts/cli.md)

The current script (`evals/run.sh`, 7 lines) loops over the samples with `python3` and asserts nothing; it is replaced, not extended. A candidate "really starts" when `"$cand" -c "import sys"` succeeds, which the Store stub fails.

**Fallback:** insufficient or contradicted by the code → read [sad.md](../sad.md) §5, §11 and [cli.md](../contracts/cli.md) §1 in full. Do not guess.

## Data delta

No DB changes.

## API contract

- `bash evals/run.sh [--plugin NAME] [--root DIR]` — every argument is passed through unchanged; the exit code is the runner's.

— `contracts/cli.md §1, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-16 — domain invariant: the outcome is usable without reading the report

> **Given** any run of the check
> **When** the run ends
> **Then** its outcome, success or failure, can be acted on automatically by the next step without reading the report
>
> — `spec.md §5, AC-16, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Rewrite `evals/run.sh`: change to the script's own folder, probe `python3`, `python`, `py` in that order with `-c "import sys"`, `exec` the first that works with `evals/run_eval.py "$@"`.
- [ ] If none works, print a one-line error to stderr and `exit 1`.
- [ ] Keep the file free of verdict logic and of any flag of its own.

## Edge cases

| Case | Behaviour |
|---|---|
| `python3` is the Store stub | probe fails, `python` is used |
| No Python at all | message on stderr, exit 1 |
| Arguments with spaces (`--root "G:/a b"`) | passed through intact |
| Run from another working directory | still finds `run_eval.py` by the script's own location |
| Runner fails | `bash evals/run.sh; echo $?` prints 1 |

## Definition of Done

- [ ] In Git Bash, `bash evals/run.sh` prints the report and exits with the runner's code (0 and 1 both observed, the 1 via `--plugin ukr-text-unknown`).
- [ ] `bash evals/run.sh --plugin ukr-text-unknown` exits 1.
- [ ] The script contains no band, verdict or counting logic.
