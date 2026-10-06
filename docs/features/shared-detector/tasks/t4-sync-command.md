---
id: T4
title: "Add the sync command: validate the carry list, rewrite or create diverged copies, never delete"
layer: "app"
deps: ["T2", "T3"]
blocks: ["T8", "T9"]
acs: ["AC-01", "AC-02", "AC-03", "AC-03b", "AC-10"]
files_hint: ["tools/shared_sync.py", "tools/tests/test_shared_sync.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T4 — Add the sync command: validate the carry list, rewrite or create diverged copies, never delete

## Place in the sequence

- **Blocked by:** T2 — plan core, T3 — check command · **Blocks:** T8 — README and architecture map, T9 — acceptance run · **Wave:** 3, reuses the plan and the report of T2/T3.
- **Lane:** shares `tools/shared_sync.py` and `tools/tests/test_shared_sync.py` with T2, T3, T5 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** one run that rewrites every diverged plugin copy from the shared source and lists what it rewrote
> **So that** I see exactly what changed in which plugin.
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task adds the write side: the only code that changes a plugin copy.

## Inlined context

> Flow 1 «sync»: read the carry list and the shared files. Could not run → `error shared.cannot_run`, exit 4. Carry entry wrong → names it, nothing is written, `result: failed`. Valid → compare every carried copy byte for byte, rewrite or create each diverged or missing copy, list each file and plugin rewritten or created, or say all copies are up to date. Optionally, a plugin holds a shared file the carry list does not give it → list it as left in place, delete by hand, and say the check still fails.
>
> — `sad.md §6, critical flow 1, abridged` · full text: [sad.md](../sad.md)

> `sync`: reads the working folder; writes only `plugins/<p>/skills/<p>/<shared path>` for validated carry-list entries; never deletes. `--staged` is valid only with `check`; `sync --staged` is a usage error → exit 4. Output lines: `rewrote <file> <plugin>`, `created <file> <plugin>`, `all copies are up to date`, `left in place, delete by hand: <file> <plugin>`, then `result: passed|failed`. Exit codes: 0 every copy equals the shared source after the run; 3 stopped by a wrong carry list, or an unlisted file or an uncarried shared file remains after the run; 4 could not run.
>
> — `contracts/cli.md, §Command + §Output + §Exit codes, abridged` · full text: [cli.md](../contracts/cli.md)

> **Hard rule:** the sync writes only to `plugins/<p>/skills/<p>/<shared path>` for entries of the carry list that passed validation; an absolute path, a path with `..` or one that leaves the plugin folder is rejected before anything is written. The whole carry list is validated first, then written. Files are written as bytes with no line-ending translation; a missing folder is created only inside the carrying plugin. Each copy is written directly (no temporary file — accepted debt).
>
> — `sad.md §8, Authentication/authorization + Paths and bytes + Write order, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** `sync` is idempotent — the first run on the current files and the second run in a row rewrite 0 files; it deletes 0 files; it never prints «all copies are up to date» while an unlisted file or an uncarried shared file exists; ≤ 2 s for 5 shared files in 3 plugins.
>
> — `sad.md §10 QG-2 + contracts/cli.md §Behavioural guarantees, abridged` · full text: [sad.md](../sad.md)

> Decided 2026-10-05: the sync does not delete a file a plugin holds that the carry list does not give it — it only warns; the check reports the file and the plugin author deletes it, because a deletion cannot be undone by the sync.
>
> — `spec.md §8, open question 1 (resolved), abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read [cli.md](../contracts/cli.md), [sad.md](../sad.md), [spec.md](../spec.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

- `python tools/shared_sync.py sync` → exit `0` (all copies equal after the run), `3` (wrong carry list, nothing written; or unlisted/uncarried file remains), `4` (could not run).
- Lines: `rewrote`, `created`, `left in place, delete by hand:`, `all copies are up to date`, `error shared.carry_entry|shared.unlisted|shared.orphan_source`, `result:`.

— `contracts/cli.md, §Command + §Output, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-01 — happy path

> **Given** the plugin author has changed a shared file in the shared source
> **When** the plugin author runs the sync
> **Then** every plugin copy of that file named in the carry list equals the shared source, a copy that was missing is created together with the folders it needs inside that plugin, and the plugin author sees a list of each file and plugin that was rewritten or created
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-02 — happy path

> **Given** every plugin copy already equals the shared source
> **When** the plugin author runs the sync
> **Then** nothing is rewritten and the output says that all copies are up to date
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-03 — error

> **Given** the carry list names a file that the shared source does not hold, or names a plugin that does not exist (no folder of that name under `plugins/`), or has an entry that leads outside a plugin folder
> **When** the plugin author runs the sync
> **Then** the sync stops before writing anything and tells the plugin author which entry of the carry list is wrong
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-03b — error

> **Given** a plugin holds a shared file that the carry list does not give it
> **When** the plugin author runs the sync
> **Then** the sync still brings every other copy up to date, leaves that file in place, lists it as «left in place, delete by hand», and ends by saying that the divergence check will still fail until it is deleted; the sync never says that all copies are up to date while such a file exists
>
> — `spec.md §5, AC-03b, verbatim` · full text: [spec.md](../spec.md)

### AC-10 — authorization: a plugin copy is not a place to edit

> **Given** the plugin author has changed a plugin copy directly and not the shared source
> **When** the plugin author runs the divergence check or the sync
> **Then** the check reports the copy as diverged, the sync overwrites it from the shared source and lists it, and the sync touches nothing outside the plugin copies named in the carry list
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `tools/shared_sync.py`: `apply_plan(plan, source, writer)` — validate (T2) → if wrong entry or orphan source: write nothing, report, exit 3.
- [ ] Write bytes (`open(..., "wb")`), `os.makedirs` only inside `plugins/<p>/skills/<p>/`; list `rewrote` vs `created`.
- [ ] Unlisted files: leave in place, print `left in place, delete by hand: …` and the `shared.unlisted` line; exit 3; never print «all copies are up to date».
- [ ] `main`: add `sync`; `sync --staged` → usage error exit 4.
- [ ] Tests (in-memory writer counting writes): rewrite + create; second run writes 0; `../x` writes 0; unlisted survives and exit 3; copies outside the carry list untouched.

## Edge cases

| Case | Behaviour |
|---|---|
| Carry entry `../x` | `shared.carry_entry`, 0 files written, exit 3 |
| Shared file that no plugin carries | `shared.orphan_source`, 0 files written, exit 3 (validated before writing) |
| Missing copy with missing `references/` folder | folder created inside that plugin only, copy listed as `created` |
| Unlisted file plus a diverged copy | diverged copy rewritten, unlisted file listed and left, exit 3 |
| Write fails (permission, disk) | `shared.cannot_run` with the reason, exit 4; the next sync repairs a short copy |
| Plugin copy changed by hand | overwritten from `shared/` and listed (the change is lost — the check's notice warns about it) |

## Definition of Done

- [ ] unit tests for AC-01, AC-02, AC-03, AC-03b, AC-10 pass; the write count is 0 on a second run
- [ ] `sync` on the real repository rewrites 0 files and prints `all copies are up to date`
- [ ] a test proves no file is deleted in any branch
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
