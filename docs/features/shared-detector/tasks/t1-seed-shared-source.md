---
id: T1
title: "Seed shared/ from the current plugin copies, add carry.json and the .gitattributes line-ending pin"
layer: "infra"
deps: []
blocks: ["T3", "T9"]
acs: ["AC-14"]
files_hint: ["shared/", ".gitattributes"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "S"
status: "todo"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T1 — Seed shared/ from the current plugin copies, add carry.json and the .gitattributes line-ending pin

## Place in the sequence

- **Blocked by:** — · **Blocks:** T3 (check command needs a real `shared/` to pass on), T9 (acceptance run) · **Wave:** 1, no dependencies; runs in parallel with T2.
- **Lane:** own lane (`shared/`, `.gitattributes` touch no other task's files).

## Why (user story)

> **As a** plugin author
> **I want** to edit each shared file in one place
> **So that** a fix to the detector or a rule list is made once instead of in two or three plugins.
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task creates the one place: the shared source and the list of who carries what.

## Inlined context

> Checked on 2026-10-04: within each shared file, all plugin copies are byte-for-byte identical today (the analyzer in 3 plugins, the syntax-figures file in 3, and the other three files in 2 each), so the shared source can be seeded from any copy and the first sync rewrites nothing.
>
> — `spec.md §1, Context, abridged` · full text: [spec.md](../spec.md)

> **Decision:** `shared/` mirrors the in-skill paths, and `shared/carry.json` maps each shared path to the plugins that carry it — for example `shared/scripts/analyze.py` is copied to `plugins/<p>/skills/<p>/scripts/analyze.py` for every plugin `<p>` listed under `scripts/analyze.py`. `carry.json` is the only file under `shared/` that is not a shared file.
>
> — `adr/0003, Decision outcome + Consequences, abridged` · full text: [0003](../adr/0003-mirror-in-skill-paths-under-shared-with-a-json-carry-list.md)

> Carry list: object `{ "<in-skill path>": ["<plugin>", ...], ... }` — keys are relative paths with forward slashes; plugin names are folder names under `plugins/`. Shared source: 5 files: `scripts/analyze.py`, `references/ai-markers.md`, `references/lexicon.md`, `references/style-toolkit.md`, `references/syntax-figures.md`.
>
> — `contracts/cli.md, §Inputs, abridged` · full text: [cli.md](../contracts/cli.md)

> A committed `.gitattributes` sets `eol=lf` for `shared/` and for the paths of the plugin copies (`plugins/*/skills/*/scripts/analyze.py` and `plugins/*/skills/*/references/` for the four reference files). The pin changes no file content, because the shared files already use LF, so the first sync still rewrites nothing.
>
> — `spec.md §8, line-endings open question (resolved 2026-10-05), abridged` · full text: [spec.md](../spec.md)

> **Hard rule:** 0 changed lines in the eval runner and in its unit tests; no file is added to, removed from or moved in any plugin folder.
>
> — `spec.md §6 (Unchanged eval) + §5 AC-14, abridged` · full text: [spec.md](../spec.md)

Carry data to write (derived from `git ls-files plugins`, 12 copies): `scripts/analyze.py` and `references/syntax-figures.md` → guard, detector, editor; `references/ai-markers.md` → guard, detector; `references/lexicon.md` and `references/style-toolkit.md` → guard, editor.

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md), [sad.md](../sad.md), [adr/](../adr/) and follow them. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-14 — cross-context

> **Given** the sync has run and its result is committed
> **When** the plugin author compares the folder of each of the three plugins in the repository before and after the step
> **Then** every file that the plugin's skill description tells Claude to read is present on the same path as before the step, and no file was added, removed or moved
>
> — `spec.md §5, AC-14, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Copy each of the 5 files byte for byte from one plugin copy into `shared/scripts/analyze.py` and `shared/references/*.md` — use a binary copy (`cp`), not an editor.
- [ ] Write `shared/carry.json` with the carry data above (UTF-8, LF, forward slashes).
- [ ] Add `.gitattributes` with `eol=lf` for `shared/` and the plugin copy paths named above.
- [ ] Verify every `shared/` file is identical to every plugin copy (`cmp`), and `git diff --stat -- plugins evals` is empty.

## Edge cases

| Case | Behaviour |
|---|---|
| A plugin copy turns out to differ from another | Not expected (checked 2026-10-04). Stop and report it; do not pick a winner silently. |
| `core.autocrlf` is `true` on the machine | `.gitattributes` `eol=lf` keeps the staged bytes LF; confirm with `git ls-files --eol`. |

## Definition of Done

- [ ] `cmp` finds all 12 plugin copies byte-identical to their `shared/` file.
- [ ] `git ls-files --eol` shows `i/lf w/lf` for every `shared/` file and every plugin copy.
- [ ] `git diff --stat` shows no change under `plugins/`, `evals/run_eval.py` or `evals/tests/`.
- [ ] every Hard Rule inlined above still holds
