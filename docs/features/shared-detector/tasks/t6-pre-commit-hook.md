---
id: T6
title: "Add the .githooks/pre-commit hook that refuses the commit on divergence or when the check cannot run"
layer: "wiring"
deps: ["T5"]
blocks: ["T8"]
acs: ["AC-08", "AC-08b"]
files_hint: [".githooks/pre-commit", "tools/tests/test_pre_commit_hook.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T6 — Add the .githooks/pre-commit hook that refuses the commit on divergence or when the check cannot run

## Place in the sequence

- **Blocked by:** T5 — Git index reader and `--staged` · **Blocks:** T8 — README and architecture map · **Wave:** 4, needs `check --staged`.
- **Lane:** own lane (`.githooks/`, its own test file); runs in parallel with T7.

## Why (user story)

> **As a** plugin author
> **I want** the check to run on demand, at the start of the eval's shell entry point and before every commit
> **So that** forgetting one path does not leave the copies unchecked.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task delivers the before-commit path: a thin Bash caller of `check --staged`.

## Inlined context

> **Decision (ADR-0002):** a committed `.githooks/pre-commit` activated by `git config core.hooksPath .githooks`. The hook that runs is always the committed file, so it cannot go stale on a clone; one command of setup, no dependency. Negative: `core.hooksPath` replaces the whole hooks folder of that clone, so any other hook in `.git/hooks/` stops running; on Linux and macOS the file must be committed with the executable bit (`git update-index --chmod=+x`).
>
> — `adr/0002, Decision outcome + Consequences, abridged` · full text: [0002](../adr/0002-ship-the-hook-in-githooks-with-core-hookspath.md)

> `.githooks/pre-commit` calls `check --staged` on every commit, whatever files it touches. Exit code read as: 0 → allow; 3 → refuse with the report; 4 or no interpreter → refuse, print the reason and «a conscious bypass is `git commit --no-verify`».
>
> — `contracts/cli.md, §Callers, abridged` · full text: [cli.md](../contracts/cli.md)

> **Interpreter lookup:** `python3`, `python`, `py` in this order; the first that runs `-c "import sys"`. Identical in `evals/run.sh` and in the hook. When none works, the hook refuses the commit (AC-08b).
>
> — `sad.md §8, Interpreter lookup, abridged` · full text: [sad.md](../sad.md)

> Flow 2: Git → hook → `check --staged`. Passed → allow the commit. A divergence → refuse with the report naming each file and plugin. The check could not run → refuse the commit with the reason and the no-verify bypass.
>
> — `sad.md §6, critical flow 2, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** the hook calls the script as `$here/../tools/shared_sync.py` where `here` is the folder of the hook itself (resolved from `$0`, not the current folder); it never passes `sync`; Bash that works in Git Bash on Windows.
>
> — `contracts/cli.md, §Command + §Callers, abridged` · full text: [cli.md](../contracts/cli.md)

**Fallback:** insufficient or contradicted by the code → read [ADR-0002](../adr/0002-ship-the-hook-in-githooks-with-core-hookspath.md), [cli.md](../contracts/cli.md), [sad.md](../sad.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. (The hook only calls `check --staged` and maps its exit code, per `contracts/cli.md §Callers`.)

## Acceptance criteria

### AC-08 — error

> **Given** the plugin author has done the one-time setup in this clone and the content about to be committed holds a diverged plugin copy
> **When** the plugin author tries to commit
> **Then** the commit is refused with the divergence report, and the check judges the content being committed, not the files left in the working folder; it judges both the shared source and the plugin copies as they are being committed, and it runs before every commit, whatever files the commit touches
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

### AC-08b — error

> **Given** the plugin author has done the one-time setup and the check cannot run, because no working interpreter is found or the check itself fails
> **When** the plugin author tries to commit
> **Then** the commit is refused with a message that says the check could not run, gives the reason, and says that a conscious bypass is `git commit --no-verify`
>
> — `spec.md §5, AC-08b, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `.githooks/pre-commit`: `#!/usr/bin/env bash`, resolve `here`, interpreter loop `python3 python py`, run `check --staged`, map exit 0/3/4 as above; no interpreter → message + non-zero.
- [ ] Mark executable in the index: `git update-index --chmod=+x .githooks/pre-commit`.
- [ ] `tools/tests/test_pre_commit_hook.py`: in a temporary Git repository with the repo files copied and `core.hooksPath` set — a staged divergence is refused (commit fails, report visible); a clean commit passes; a PATH with no interpreter / a broken script gives the «could not run … `git commit --no-verify`» message and refuses.
- [ ] Comments in Ukrainian, messages in English (as `evals/run.sh`).

## Edge cases

| Case | Behaviour |
|---|---|
| No working interpreter | commit refused, message says the check could not run, reason «no working Python found», and the `--no-verify` bypass |
| `check` exits 4 (e.g. Git failure, malformed `carry.json`) | commit refused with the reason and the bypass |
| `check` exits 3 | commit refused with the divergence report on stdout |
| Commit touches only a README | the check still runs |
| `git commit --no-verify` | hook not run (conscious bypass; README states the limit) |
| Hook set up from a subfolder | `here` comes from `$0`, not the working folder |

## Definition of Done

- [ ] hook test refuses a staged divergence and allows a clean commit
- [ ] hook test refuses with the «could not run» message when the check cannot run
- [ ] `git ls-files --stage .githooks/pre-commit` shows mode `100755`
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
