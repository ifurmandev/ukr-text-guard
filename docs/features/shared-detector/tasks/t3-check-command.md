---
id: T3
title: "Add the check command: working-folder reader, report rendering, overwrite notice and the 0/3/4 exit-code contract"
layer: "ports"
deps: ["T1", "T2"]
blocks: ["T4", "T5", "T7"]
acs: ["AC-03c", "AC-04", "AC-05"]
files_hint: ["tools/shared_sync.py", "tools/tests/test_shared_sync.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T3 — Add the check command: working-folder reader, report rendering, overwrite notice and the 0/3/4 exit-code contract

## Place in the sequence

- **Blocked by:** T1 — seed shared/ …, T2 — plan core · **Blocks:** T4 — sync, T5 — staged reader, T7 — evals/run.sh · **Wave:** 2, needs the plan (T2) and a real `shared/` to pass on (T1).
- **Lane:** shares `tools/shared_sync.py` and `tools/tests/test_shared_sync.py` with T2, T4, T5 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** a check that fails when any plugin copy differs from the shared source and names each file and plugin
> **So that** a missed copy cannot reach a release unseen.
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task puts a command line, a report and exit codes on top of the plan from T2.

## Inlined context

> `python tools/shared_sync.py <command> [--staged]`. The repository root is the parent of the folder that holds the script (the parent of `tools/`), found from its own location, not from the current working folder. No `--root` flag. `check` (no flag) reads the working folder and writes nothing in any branch. An unknown command, an unknown flag or no command is a usage error → exit 4 with `error shared.cannot_run: usage ...`. No stdin, no environment variable, no config file besides `shared/carry.json`.
>
> — `contracts/cli.md, §Command, abridged` · full text: [cli.md](../contracts/cli.md)

> Stdout carries the report; stderr carries only `shared.cannot_run` and usage text. Every line is English: `error shared.<code>: <file> <plugin> <detail>`. The last line is always `result: passed` or `result: failed`. On `check`, the overwrite notice is printed once whenever a copy differs:
> `note: plugin copies are overwritten by the shared source (shared/); a change made in a copy must be moved to shared/ before running sync`
> Passed run: `checked 12 files in 3 plugins` then `result: passed`.
>
> — `contracts/cli.md, §Output + Examples, abridged` · full text: [cli.md](../contracts/cli.md)

> Exit codes for `check`: 0 every copy equals the shared source and matches the carry list; 3 any divergence, a wrong carry list, or an uncarried shared file; 4 could not run, including usage errors and any unexpected exception (`main` catches it; the Python default 1 is never returned).
>
> — `contracts/cli.md, §Exit codes, abridged` · full text: [cli.md](../contracts/cli.md)

> Flow 4 «check on demand»: precondition: the check only reads, it writes no file in any branch. Wrong carry list or uncarried shared file → names it, `result: failed`, exit 3. Valid list → compare every carried copy, look for unlisted files; all equal → `result: passed` + count, exit 0; otherwise name each file and plugin as differing, missing, unlisted or differing only in line endings, print the overwrite notice, exit 3. Could not run → `error shared.cannot_run` with the reason, exit 4. Postcondition: no file changed.
>
> — `sad.md §6, critical flow 4, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** the check ≤ 2 s for 5 shared files in 3 plugins; standard library only; Python 3.8+. Guard clauses return a finding, not an exception; the plan is a plain value that the report renders.
>
> — `spec.md §6 (Duration) + sad.md §8 (Error handling), abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read [cli.md](../contracts/cli.md), [sad.md](../sad.md), [spec.md](../spec.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

- `python tools/shared_sync.py check` → exit `0` (`result: passed`), `3` (`result: failed`, findings on stdout), `4` (`error shared.cannot_run: …` on stderr).
- Findings it renders: `shared.differing`, `shared.line_endings`, `shared.missing`, `shared.unlisted`, `shared.orphan_source`, `shared.carry_entry`; `shared.cannot_run` for unreadable files, malformed `carry.json`, usage errors, any unexpected exception.

— `contracts/cli.md, §Command + §Output, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-03c — error

> **Given** the carry list is wrong in one of the ways of AC-03, or the shared source holds a file that no plugin carries
> **When** the plugin author runs the divergence check
> **Then** the check fails, names the wrong carry list entry or the file that no plugin carries, and writes nothing
>
> — `spec.md §5, AC-03c, verbatim` · full text: [spec.md](../spec.md)

### AC-04 — happy path

> **Given** every plugin copy equals the shared source and matches the carry list
> **When** the plugin author runs the divergence check
> **Then** the check passes and states how many files in how many plugins it compared
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-05 — error

> **Given** a plugin copy differs from the shared source
> **When** the plugin author runs the divergence check
> **Then** the check fails, names each differing file and plugin, and says that copies are overwritten by the shared source, so a change made in a copy must be moved to the shared source before the sync
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `tools/shared_sync.py`: working-folder `TreeReader` (bytes via `open(..., "rb")`, forward-slash relative paths, repo root from `__file__`).
- [ ] Render the plan: finding lines, overwrite notice (once, only when a copy differs/missing/line-endings), `checked N files in M plugins`, final `result:` line.
- [ ] `main(argv)`: parse `check`; usage errors → stderr `error shared.cannot_run: usage …`, exit 4; wrap everything in `try/except Exception` → exit 4 (never 1).
- [ ] Tests: passed run counts (12 files, 3 plugins on the real repo); divergence run names file+plugin and prints the notice; wrong carry list; a snapshot test that `check` writes nothing (tree unchanged); exit codes 0/3/4.

## Edge cases

| Case | Behaviour |
|---|---|
| `carry.json` missing or malformed JSON | `error shared.cannot_run: <reason>` on stderr, exit 4 |
| Unreadable plugin copy (permission) | `shared.cannot_run`, exit 4, not a divergence |
| No command / unknown command / unknown flag | usage error, exit 4 |
| Only an unlisted or orphan finding exists | exit 3; the overwrite notice is printed only if a copy differs |
| Unexpected exception | caught in `main`, exit 4 |

## Definition of Done

- [ ] unit tests for AC-03c, AC-04, AC-05 pass; `check` against the real repo prints `checked 12 files in 3 plugins` and exits 0
- [ ] exit codes 1 and 2 are never produced (test covers an injected exception)
- [ ] a timed run takes ≤ 2 s
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
