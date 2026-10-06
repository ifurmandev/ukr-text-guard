---
id: T8
title: "Document the shared source, the one-time hook setup and the checked eval path in README and architecture map"
layer: "docs"
deps: ["T4", "T6", "T7"]
blocks: ["T9"]
acs: ["AC-09", "AC-11"]
files_hint: ["README.md", "docs/architecture-map.md"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T8 — Document the shared source, the one-time hook setup and the checked eval path in README and architecture map

## Place in the sequence

- **Blocked by:** T4 — sync, T6 — hook, T7 — run.sh · **Blocks:** T9 — acceptance run · **Wave:** 5, the commands it documents must exist and behave as written.
- **Lane:** own lane (`README.md`, `docs/architecture-map.md`).

## Why (user story)

> **As a** plugin author
> **I want** the divergence report and the project documents to say that copies are overwritten by the shared source
> **So that** a change I made directly in a plugin copy is moved to the shared source instead of being silently erased.
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task writes the document half of that story and the setup instructions of US-04.

## Inlined context

> Commands to document (from `contracts/cli.md`): on-demand check `python tools/shared_sync.py check`; sync `python tools/shared_sync.py sync`; one-time hook setup `git config core.hooksPath .githooks` (ADR-0002); the eval path `bash evals/run.sh` (runs the check first, exit 3 divergence / 4 could not run). Staged vs working content: the hook judges the Git index, `check` and `run.sh` judge the working folder.
>
> — `contracts/cli.md, §Command + §Callers, abridged` · full text: [cli.md](../contracts/cli.md)

> The README states: the one-time setup for the before-commit step; that without it only the on-demand check and the eval entry point protect; that `core.hooksPath` hides any other hook kept in `.git/hooks/` of that clone; which content each entry point judges (the staged check judges the index, the others the working folder); the reasons for carry decisions (JSON has no comments); that a direct run of `run_eval.py` does not perform the check.
>
> — `sad.md §11 + ADR-0002/0003 Consequences, abridged` · full text: [sad.md](../sad.md)

> Current README (Ukrainian): the section that runs the analyzer shows `python3 plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py текст.txt` and mentions `evals/run.sh`; the eval table is «прогін `bash evals/run.sh` на копії детектора з плагіна `ukr-text-guard`, 3 жовтня 2026 року». The architecture map «Where things live» says a change to detection logic → `scripts/analyze.py`, «currently three byte-identical copies (see debt below)».
>
> — `README.md + docs/architecture-map.md, current text, abridged` · full text: [README.md](../../../../README.md)

> **Hard rule:** README and product text are in Ukrainian; the architecture map is in English. Do not change the committed eval table or any numbers in it. The architecture map must say that the sync must be run after editing `shared/` and that `evals/run.sh` is the only eval path that performs the divergence check.
>
> — `sad.md §2 Conventions + spec.md §5 AC-11, abridged` · full text: [spec.md](../spec.md)

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md), [cli.md](../contracts/cli.md), [sad.md](../sad.md) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-09 — cross-context

> **Given** the step is shipped
> **When** the plugin author reads the README
> **Then** the README names the one-time setup for the before-commit step, states that without it only the on-demand check and the eval entry point protect, and shows the command for the on-demand check and for the sync
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

### AC-11 — cross-context

> **Given** the step is shipped
> **When** the plugin author reads the README section on running the analyzer and the architecture map section on where to change detection logic or a rule list
> **Then** both name the shared source as the place to edit and say that the sync must be run afterwards, and both name the eval's shell entry point as the only eval path that performs the divergence check, saying that a direct run of the eval runner does not
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `README.md` (Ukrainian): new section for the shared files — edit only in `shared/`, then run `python tools/shared_sync.py sync`; `check` command; carry-list reasons; one-time setup `git config core.hooksPath .githooks` with the limit sentence and the `core.hooksPath` side effect; which content each entry point judges.
- [ ] `README.md`, section on running the analyzer: name `shared/scripts/analyze.py` as the place to edit, the sync afterwards, and `bash evals/run.sh` as the only eval path that checks (a direct `run_eval.py` does not).
- [ ] `docs/architecture-map.md`: update «Where things live» (shared source, sync, check, hook, carry list), the duplication debt text and the tooling in the evals row; same two statements as the README.
- [ ] Leave the committed eval table and its numbers unchanged.

## Edge cases

| Case | Behaviour |
|---|---|
| Reader skips the hook setup | README states that then only `check` and `run.sh` protect |
| Reader edits a plugin copy | README and architecture map say it will be overwritten and the check reports it |
| Reader runs `python evals/run_eval.py` directly | both documents say this path does not perform the check |

## Definition of Done

- [ ] README contains the setup command, the limit sentence, the `check` and `sync` commands (AC-09 read-through)
- [ ] README analyzer section and architecture map name `shared/` as the edit place, the sync afterwards, and `evals/run.sh` as the only checked eval path (AC-11 read-through)
- [ ] the commands written in the documents are run once and behave as described
- [ ] every Hard Rule inlined above still holds
