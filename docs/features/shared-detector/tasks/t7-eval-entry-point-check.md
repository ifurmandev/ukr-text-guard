---
id: T7
title: "Extend evals/run.sh to run the check first and end with exit code 3 or 4 on divergence"
layer: "wiring"
deps: ["T3"]
blocks: ["T8", "T9"]
acs: ["AC-07"]
files_hint: ["evals/run.sh", "tools/tests/test_run_sh.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T7 — Extend evals/run.sh to run the check first and end with exit code 3 or 4 on divergence

## Place in the sequence

- **Blocked by:** T3 — check command · **Blocks:** T8 — README and architecture map, T9 — acceptance run · **Wave:** 3, needs only `check`; runs in parallel with T4/T5/T6.
- **Lane:** own lane (`evals/run.sh`, its own test file). `evals/run_eval.py` and `evals/tests/` are never touched.

## Why (user story)

> **As a** plugin author
> **I want** the check to run on demand, at the start of the eval's shell entry point and before every commit
> **So that** forgetting one path does not leave the copies unchecked.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task delivers the eval path: no sample is measured while the copies differ.

## Inlined context

> `evals/run.sh` (extended) calls `<interpreter> "$here/../tools/shared_sync.py" check` on the whole repository, before any sample, whatever arguments `run.sh` received. Exit 0 → run `run_eval.py` with the original arguments; 3 → print «the eval did not run, the cause is a divergence», exit 3; 4 → print «the eval did not run, the check could not run», exit 4. No interpreter found → message and exit 4 (today 1).
>
> — `contracts/cli.md, §Callers, abridged` · full text: [cli.md](../contracts/cli.md)

> Current `evals/run.sh`: finds the first of `python3`, `python`, `py` that runs `-c "import sys"` and `exec`s `"$here/run_eval.py" "$@"`; with none, prints `run.sh: no working Python found (tried python3, python, py)` to stderr and exits 1. Comments are in Ukrainian; `here="$(cd "$(dirname "$0")" && pwd)"`.
>
> — `evals/run.sh, current file, abridged` · full text: [run.sh](../../../../evals/run.sh)

> Flow 3: `run.sh` → check the whole repository; passed → run all samples, the runner's report and exit code 0 or 1; divergence → «the eval did not run, the cause is a divergence», exit 3; could not run → «the eval did not run, the check could not run», exit 4. The runner uses 0 (all bands pass) and 1 (a band failed), so 3 and 4 let a script tell the three outcomes apart.
>
> — `sad.md §6, critical flow 3 + §4 choice 3, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** 0 changed lines in `evals/run_eval.py` and in `evals/tests/`; 74 of 74 existing unit tests still pass. The README and the architecture map name `evals/run.sh` as the only checked eval path (a direct run of `run_eval.py` is unchecked — see T8).
>
> — `spec.md §6 (Unchanged eval) + §8 (resolved), abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read [cli.md](../contracts/cli.md), [sad.md](../sad.md), [spec.md](../spec.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. (Exit codes of `evals/run.sh`: `0`/`1` from the runner when the check passes; `3` divergence; `4` check could not run or no interpreter.)

## Acceptance criteria

### AC-07 — error

> **Given** the copies differ
> **When** the plugin author starts the eval through its shell entry point
> **Then** the divergence is reported, the run stops before any sample is measured, and the output states that the eval did not run and that the cause is a divergence, not a failed band; the run ends with a result code that differs from both success and a failed band, so a script can tell the three apart; the entry point always checks the whole repository that holds it, all plugins, whatever arguments it was given
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `evals/run.sh`: after finding the interpreter, run `"$cand" "$here/../tools/shared_sync.py" check` (no `--staged`, ignoring `run.sh` arguments), pass its stdout/stderr through.
- [ ] Map: 0 → `exec "$cand" "$here/run_eval.py" "$@"`; 3 → «run.sh: the eval did not run, the cause is a divergence (not a failed band)», `exit 3`; other → «… the check could not run», `exit 4`; no interpreter → message, `exit 4`.
- [ ] `tools/tests/test_run_sh.py` (skips when `bash` is absent): a temporary repo copy with a diverged plugin copy → exit 3, message present, no sample report; broken `carry.json` → exit 4; arguments such as `--plugin ukr-text-detector` do not narrow the check.
- [ ] Confirm `git diff --stat` shows no change in `evals/run_eval.py`, `evals/tests/`.

## Edge cases

| Case | Behaviour |
|---|---|
| Copies equal | the runner runs unchanged, with the original arguments; its exit 0/1 is returned as before |
| Divergence | no sample measured, exit 3, message separates divergence from a failed band |
| Check exits 4 or crashes | exit 4, «the check could not run» |
| `run.sh --plugin ukr-text-detector` | the whole repository is still checked, all plugins |
| No Python found | message on stderr, exit 4 (was 1) |

## Definition of Done

- [ ] `test_run_sh.py` passes for exit 3 and exit 4; the clean path still reaches the runner
- [ ] `python -m unittest discover evals/tests` passes 74 of 74; `git diff --stat` shows no change under `evals/run_eval.py`, `evals/tests/`
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
