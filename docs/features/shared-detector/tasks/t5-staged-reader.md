---
id: T5
title: "Add the Git index tree reader and the check --staged flag"
layer: "infra"
deps: ["T3"]
blocks: ["T6"]
acs: ["AC-08"]
files_hint: ["tools/shared_sync.py", "tools/tests/test_shared_sync.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T5 — Add the Git index tree reader and the check --staged flag

## Place in the sequence

- **Blocked by:** T3 — check command · **Blocks:** T6 — pre-commit hook · **Wave:** 3, the `TreeReader` interface and the `check` command must exist first.
- **Lane:** shares `tools/shared_sync.py` and `tools/tests/test_shared_sync.py` with T2, T3, T4 — serialized with T4 (no data dependency between them).

## Why (user story)

> **As a** plugin author
> **I want** the check to run on demand, at the start of the eval's shell entry point and before every commit
> **So that** forgetting one path does not leave the copies unchecked.
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task makes the check judge the content being committed (the Git index) instead of the working folder.

## Inlined context

> **Decision (ADR-0001):** the core works through a tree reader with two implementations behind one interface (list paths, read bytes): one reads the working folder, the other reads the Git index with `git ls-files` and `git cat-file`. Nothing is copied and no working file is changed. Negative: it depends on Git plumbing output (`ls-files -z`, `cat-file --batch`) and needs an integration test with a real repository; Git converts line endings when it stages (`core.autocrlf`), mitigated by the `.gitattributes` pin.
>
> — `adr/0001, Decision outcome + Consequences, abridged` · full text: [0001](../adr/0001-read-staged-content-from-the-git-index.md)

> `check --staged` reads the Git index and writes nothing in any branch. `--staged` is valid only with `check`. Stdout carries the report; stderr carries `shared.cannot_run`, e.g. `error shared.cannot_run: git index could not be read: <reason>`, exit 4. The staged reader supplies both the shared source and the carry list, so `shared/carry.json` is read from the index too.
>
> — `contracts/cli.md, §Command + §Output, abridged` · full text: [cli.md](../contracts/cli.md)

> Flow 2 «check before every commit»: the CLI reads the index → staged shared source, carry list and plugin copies; every copy equals the shared source → passed; a divergence exists → report naming each file and plugin; the check could not run → reported as exit 4.
>
> — `sad.md §6, critical flow 2, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Git 2.9 or newer; standard library only (call Git through `subprocess`); the check ≤ 2 s. QG-1 verification: one integration test on a real temporary Git repository for the index reader, including a copy that is fixed in the working folder but staged with a divergence.
>
> — `sad.md §2 + §10 QG-1, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [ADR-0001](../adr/0001-read-staged-content-from-the-git-index.md), [cli.md](../contracts/cli.md), [sad.md](../sad.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

- `python tools/shared_sync.py check --staged` → same output and exit codes as `check` (`0`/`3`/`4`), judging the Git index; a Git failure → `error shared.cannot_run: git index could not be read: <reason>`, exit `4`.

— `contracts/cli.md, §Command + §Exit codes, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-08 — error

> **Given** the plugin author has done the one-time setup in this clone and the content about to be committed holds a diverged plugin copy
> **When** the plugin author tries to commit
> **Then** the commit is refused with the divergence report, and the check judges the content being committed, not the files left in the working folder; it judges both the shared source and the plugin copies as they are being committed, and it runs before every commit, whatever files the commit touches
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

(This task delivers «judges the content being committed»; T6 delivers the refusal of the commit and «before every commit».)

## Checklist

- [ ] `tools/shared_sync.py`: `IndexTreeReader` — list with `git ls-files -z`, read blobs with `git cat-file --batch` (or `git show :<path>`), bytes only, no decoding; run Git from the repo root.
- [ ] `main`: accept `--staged` only with `check`; any Git failure → `shared.cannot_run` on stderr, exit 4.
- [ ] Integration test in a real temporary Git repository (`tempfile` + `git init`): staged divergence with the working folder fixed → exit 3; staged equal with the working folder diverged → exit 0; a staged `shared/` change is judged as staged.
- [ ] Test: a directory that is not a Git repository → exit 4 with the reason.

## Edge cases

| Case | Behaviour |
|---|---|
| Working copy fixed but the diverged copy is staged | `check --staged` fails (exit 3) |
| Working copy diverged but the equal copy is staged | `check --staged` passes (exit 0) |
| `shared/carry.json` staged with a wrong entry | exit 3, wrong entry named |
| `git` not found / not a repository / index unreadable | `shared.cannot_run: git index could not be read: <reason>`, exit 4 |
| Commit touches only unrelated files | still checks everything — no path filtering |
| File path with non-ASCII or spaces | `-z` listing keeps it intact |

## Definition of Done

- [ ] integration test on a real temporary Git repository passes for both mixed cases
- [ ] `check --staged` changes no file in the working folder or the index
- [ ] a timed run takes ≤ 2 s
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
