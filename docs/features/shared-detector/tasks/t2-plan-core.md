---
id: T2
title: "Build the plan core: tree reader interface, carry-list validation and the byte comparator with all divergence kinds"
layer: "domain"
deps: []
blocks: ["T3", "T4"]
acs: ["AC-03", "AC-06", "AC-12"]
files_hint: ["tools/shared_sync.py", "tools/tests/test_shared_sync.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T2 — Build the plan core: tree reader interface, carry-list validation and the byte comparator with all divergence kinds

## Place in the sequence

- **Blocked by:** — · **Blocks:** T3 (check command), T4 (sync) · **Wave:** 1, pure functions on an in-memory tree need neither `shared/` nor Git; runs in parallel with T1.
- **Lane:** shares `tools/shared_sync.py` and `tools/tests/test_shared_sync.py` with T3, T4, T5 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** a carry list that says which plugin carries which shared file, and a check that reports a missing or an unlisted file
> **So that** a plugin never lacks a file its skill description tells Claude to read and never holds a stale one.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task builds the plan: the one value that classifies every copy as equal, differing, line-endings-only, missing or unlisted, and every carry-list entry as valid or wrong.

## Inlined context

> The core builds a plan from three inputs: the shared source, the carry list and a tree of plugin copies. `check` renders the plan and never writes. `sync` validates the carry list first, then applies the plan, then renders it. Both use the same comparator, so the sync can never write something the check would still call a divergence.
>
> — `sad.md §4, choice 1 «One plan, two commands», abridged` · full text: [sad.md](../sad.md)

> There is no layering to speak of: the product is one Python command made of pure functions (read a tree, load the carry list, build a plan, render it, apply it) behind a thin argument parser. The plan is a plain value, so the check, the sync and the tests all consume the same thing. `tools/shared_sync.py`: tree readers, carry list, plan, report, apply, exit codes.
>
> — `sad.md §5, intro + decomposition, abridged` · full text: [sad.md](../sad.md)

> **Decision (ADR-0001):** the core works through a tree reader with two implementations behind one interface (list paths, read bytes): one reads the working folder, the other reads the Git index. One comparator and one report format for both; unit tests use an in-memory reader and need no Git.
>
> — `adr/0001, Decision outcome + Consequences, abridged` · full text: [0001](../adr/0001-read-staged-content-from-the-git-index.md)

> Carry-list entry validation (before anything is written): the key names a file the shared source holds; each plugin is a folder under `plugins/`; the resolved target stays inside that plugin folder (no absolute path, no `..`). A failure is `shared.carry_entry`. A shared file no plugin carries is `shared.orphan_source`. `carry.json` is excluded from the shared files by its fixed name. A plugin copy lives at `plugins/<p>/skills/<p>/<in-skill path>`.
>
> — `contracts/cli.md, §Inputs, abridged` + `adr/0003, Consequences` · full text: [cli.md](../contracts/cli.md)

> Codes: `shared.differing`, `shared.line_endings`, `shared.missing`, `shared.unlisted`, `shared.orphan_source`, `shared.carry_entry`. A copy that differs only in an invisible mark has no code of its own: it is `shared.differing` with the detail saying so (decided 2026-10-05). Paths in `carry.json` are relative with forward slashes. Files are compared as bytes with no line-ending translation.
>
> — `sad.md §8, Report format + Paths and bytes, abridged` · full text: [sad.md](../sad.md)

> **Hard rule:** Python 3, standard library only, no import outside it; runs on Python 3.8 or newer (no `tomllib`, no `match`). Comments and docstrings in Ukrainian; identifiers, test names and error codes in English.
>
> — `sad.md §2, Technical + Conventions, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md), [sad.md](../sad.md), [adr/](../adr/), [cli.md](../contracts/cli.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. (The plan is consumed by T3 and T4; its finding codes are those of `contracts/cli.md §Output`.)

## Acceptance criteria

### AC-03 — error

> **Given** the carry list names a file that the shared source does not hold, or names a plugin that does not exist (no folder of that name under `plugins/`), or has an entry that leads outside a plugin folder
> **When** the plugin author runs the sync
> **Then** the sync stops before writing anything and tells the plugin author which entry of the carry list is wrong
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

(This task delivers the validation function that returns the wrong entries; T4 stops the sync on it.)

### AC-06 — error

> **Given** the carry list requires a file in a plugin that the plugin does not hold, or any folder under `plugins/` holds a file at the path of a shared file that the carry list does not give that plugin
> **When** the plugin author runs the divergence check
> **Then** the check fails and names the file, the plugin and whether the copy is missing or unlisted; an unlisted file is judged only by the path of a shared file, so any other file in a plugin, including files generated by running the analyzer, is not counted
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-12 — domain invariant: copies are equal byte for byte

> **Given** a plugin copy differs from the shared source only in line endings or in an invisible mark
> **When** the plugin author runs the divergence check
> **Then** the check reports that copy as diverged, and the check changes no file in any case
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `tools/tests/test_shared_sync.py`: one test per kind on an in-memory tree — differing, missing, unlisted, line-endings-only (CRLF vs LF) — plus an invisible-mark case (e.g. U+200B) that yields `shared.differing` with the detail «differs only in an invisible mark».
- [ ] `tools/shared_sync.py`: `TreeReader` interface (list paths, read bytes) and an in-memory/working-folder implementation of it (the working-folder one is finished in T3 if the plan only needs the interface here).
- [ ] `load_carry` + `validate_carry(carry, source_paths, plugin_names)` → findings `shared.carry_entry` / `shared.orphan_source`; reject absolute paths, `..`, and keys the source does not hold.
- [ ] `build_plan(source, carry, copies)` → plain value of findings, byte comparator only; classify line-endings-only by comparing after `\r\n`→`\n`.
- [ ] Unlisted detection looks only at the paths of the shared files in every folder under `plugins/`, never at other files.

## Edge cases

| Case | Behaviour |
|---|---|
| Carry entry `../x` or an absolute path | `shared.carry_entry` «path leaves the plugin folder»; nothing else is evaluated as valid for that entry |
| Carry key not in the shared source | `shared.carry_entry` |
| Plugin in the carry list has no folder under `plugins/` | `shared.carry_entry` |
| Shared file that no plugin carries | `shared.orphan_source` |
| Copy differs in both bytes and line endings | `shared.differing` (line-endings kind only when the sole difference is `\r\n`) |
| Analyzer-generated files (e.g. `__pycache__`) in a plugin | not counted, only shared-file paths are judged |

## Definition of Done

- [ ] unit tests for the 4 divergence kinds and the carry-list guards pass (`python -m unittest discover tools/tests`)
- [ ] the in-memory plan performs no write of any kind
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
