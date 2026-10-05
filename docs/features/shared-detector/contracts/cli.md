# CLI contract — shared-detector

Derived from `spec.md` §4/§5, `sad.md` §6 (flows 1–4) and §8 (report format, exit codes). The feature changes no schema and has no datastore (sad §2), so there is no `data-model.md`; the "model" is the set of files in the repository. Interface kind: `cli` (`target_surfaces: [cli]`). The two Bash callers are thin and are described under *Callers*, not as surfaces.

Why this contract exists: one command keeps the plugin copies of the shared files equal to one shared source (`check` reports, `sync` rewrites).

## Command

```
python tools/shared_sync.py <command> [--staged]
```

`<command>` is `check` or `sync`. The interpreter is the first of `python3`, `python`, `py` that runs `-c "import sys"` (sad §8). The repository root is the parent of the folder that holds the script, that is, the parent of `tools/`; the script finds it from its own location, not from the current working folder. `evals/run.sh` calls the script as `$here/../tools/shared_sync.py`, where `here` is the folder of `run.sh` itself (`evals/`), as it already does for `run_eval.py`. No `--root` flag exists.

| Command | Flag | Reads | Writes | Spec |
|---|---|---|---|---|
| `check` | none | working folder | nothing, in every branch | AC-03c, AC-04, AC-05, AC-06, AC-10, AC-12 |
| `check` | `--staged` | Git index (ADR-0001) | nothing, in every branch | AC-08, AC-08b |
| `sync` | none | working folder | only `plugins/<p>/skills/<p>/<shared path>` for validated carry-list entries; never deletes | AC-01, AC-02, AC-03, AC-03b, AC-10 |

- `--staged` is valid only with `check`. `sync --staged`, an unknown command, an unknown flag or no command is a usage error → exit 4 with `error shared.cannot_run: usage ...`.
- No stdin, no environment variable, no config file besides `shared/carry.json`.
- The eval entry point and the hook never pass `sync`.

## Inputs (files, not parameters)

| Input | Path | Shape |
|---|---|---|
| Shared source | `shared/<in-skill path>` | 5 files: `scripts/analyze.py`, `references/ai-markers.md`, `references/lexicon.md`, `references/style-toolkit.md`, `references/syntax-figures.md` |
| Carry list | `shared/carry.json` | object `{ "<in-skill path>": ["<plugin>", ...], ... }` — keys are relative paths with forward slashes; plugin names are folder names under `plugins/` (ADR-0003) |
| Plugin copies | `plugins/<p>/skills/<p>/<in-skill path>` | compared and written as bytes, no line-ending translation (AC-12, sad §8) |

Carry-list entry validation (before anything is written): the key names a file the shared source holds; each plugin is a folder under `plugins/`; the target stays inside that plugin folder by its text (no absolute path, no `..`). A failure is `shared.carry_entry` (AC-03, AC-03c). A target that leaves the plugin folder only through a symbolic link or junction on disk (on the copy, on a sub-folder, or on the plugin folder itself) is not a carry-list error: `sync` refuses it with `shared.cannot_run`, exit 4, after checking every target and before writing the first one, so nothing is written (AC-10). A shared file no plugin carries is `shared.orphan_source` (AC-03c).

## Output

Stdout carries the report; stderr carries only `shared.cannot_run` and usage text. Every line is English. Finding lines follow the eval runner's `error <code>: <message>` shape:

```
error shared.<code>: <file> <plugin> <detail>
```

The last line is always `result: passed` or `result: failed`, except on exit 4, where the run could not start or could not finish (no interpreter — see *Callers*; an unreadable copy, a malformed `carry.json`, a usage error, a failed write). Exit 4 prints `error shared.cannot_run: <reason>` on stderr and no `result:` line; a `sync` that stops after some writes first lists on stdout the copies it already rewrote or created.

| Code | Command | Meaning | Spec |
|---|---|---|---|
| `shared.differing` | check, sync | a carried copy differs from the shared source. Also used when the only difference is an invisible mark: the detail says «differs only in an invisible mark», and no separate code exists (decided 2026-10-05, F1 in the sync report) | AC-05, AC-12 |
| `shared.line_endings` | check | the copy differs only in line endings | AC-12 |
| `shared.missing` | check, sync | the carry list requires the file in the plugin; the plugin does not hold it. `sync` creates it and lists it as *created* | AC-06 |
| `shared.unlisted` | check, sync | the plugin holds a file at the path of a shared file that the carry list does not give it. `sync` leaves it in place and lists it as «left in place, delete by hand» | AC-06, AC-03b |
| `shared.orphan_source` | check, sync | the shared source holds a file no plugin carries | AC-03c |
| `shared.carry_entry` | check, sync | a carry-list entry is wrong: absent shared file, unknown plugin, or a path leaving the plugin folder | AC-03, AC-03c |
| `shared.cannot_run` | check, sync | the run could not complete (unreadable file, malformed `carry.json`, Git failure with `--staged`, usage error, a target that leaves the plugin folder through a link, any unexpected exception) | AC-08b, AC-10 |

`error shared.differing` / `shared.line_endings` / `shared.missing` lines on `check` are followed once by the overwrite notice (printed whenever a copy differs, AC-05, AC-10):

```
note: plugin copies are overwritten by the shared source (shared/); a change made in a copy must be moved to shared/ before running sync
```

### Examples (placeholder paths only)

`check`, all equal (AC-04) — exit 0:

```
checked 12 files in 3 plugins
result: passed
```

`check`, divergence (AC-05, AC-06, AC-12) — exit 3:

```
error shared.differing: scripts/analyze.py ukr-text-detector copy differs from shared/scripts/analyze.py
error shared.line_endings: references/lexicon.md ukr-text-editor copy differs only in line endings
error shared.missing: references/ai-markers.md ukr-text-editor copy is not present
error shared.unlisted: references/style-toolkit.md ukr-text-guard file is not given to this plugin by shared/carry.json
note: plugin copies are overwritten by the shared source (shared/); a change made in a copy must be moved to shared/ before running sync
result: failed
```

`sync`, rewrote two copies (AC-01) — exit 0:

```
rewrote scripts/analyze.py ukr-text-detector
created references/ai-markers.md ukr-text-editor
result: passed
```

`sync`, nothing to do (AC-02) — exit 0:

```
all copies are up to date
result: passed
```

`sync`, wrong carry list (AC-03) — exit 3, nothing written:

```
error shared.carry_entry: references/lexicon.md ../x plugin path leaves the plugin folder
result: failed
```

`sync`, unlisted file remains (AC-03b) — exit 3; other copies were brought up to date, nothing is deleted, «all copies are up to date» is never printed:

```
rewrote scripts/analyze.py ukr-text-detector
left in place, delete by hand: references/style-toolkit.md ukr-text-guard
error shared.unlisted: references/style-toolkit.md ukr-text-guard the check still fails until this file is deleted
result: failed
```

Could not run (AC-08b) — exit 4, stderr:

```
error shared.cannot_run: git index could not be read: <reason>
```

## Exit codes

One contract for all three entry points (sad §4 choice 3, §8).

| Code | `check` | `sync` |
|---|---|---|
| 0 | every copy equals the shared source and matches the carry list | every copy equals the shared source after the run |
| 3 | any divergence, a wrong carry list, or an uncarried shared file | stopped by a wrong carry list; or an unlisted file or an uncarried shared file remains after the run |
| 4 | could not run, including usage errors and any unexpected exception (`main` catches it; the Python default 1 is never returned) | same |

Codes 1 and 2 are never produced by this command, so a caller can tell the three outcomes apart from the eval's own 0 (all bands pass) / 1 (a band failed).

## Callers

| Caller | Invocation | Reads exit code as |
|---|---|---|
| `evals/run.sh` (extended) | `<interpreter> "$here/../tools/shared_sync.py" check` on the whole repository, before any sample, whatever arguments `run.sh` received (AC-07) | 0 → run `run_eval.py` with the original arguments; 3 → print «the eval did not run, the cause is a divergence», exit 3; 4 → print «the eval did not run, the check could not run», exit 4. No interpreter found → message and exit 4 (today 1) |
| `.githooks/pre-commit` | `check --staged`, on every commit whatever files it touches (AC-08) | 0 → allow; 3 → refuse with the report; 4 or no interpreter → refuse, print the reason and «a conscious bypass is `git commit --no-verify`» (AC-08b) |
| Plugin author | `check`, `sync` from the repository root | as above |

The hook is switched on once per clone with `git config core.hooksPath .githooks` (ADR-0002); the README states this (AC-09).

## Behavioural guarantees

- `check` changes no file in any branch (AC-12, flow 4 pre/postcondition).
- `sync` is idempotent: the first run on the current files and the second run in a row rewrite 0 files (spec §6).
- `sync` validates the whole carry list first, then writes; a wrong entry means 0 files written (AC-03).
- `sync` checks every target (including links on disk) before the first write; a target that resolves outside its plugin folder means 0 files written and exit 4 (AC-10).
- `sync` writes only to carried plugin copies; a missing folder is created only inside the carrying plugin; no file is ever deleted (AC-10, AC-03b).
- `sync` never prints «all copies are up to date» while an unlisted file or an uncarried shared file exists.
- Each command takes ≤ 2 s for 5 shared files in 3 plugins (spec §6).
- Standard library only; Python 3.8 or newer (sad §2).

## Not part of the interface

AC-09, AC-11 (README and architecture-map text), AC-13 (one-off eval run on each analyzer copy), AC-14 (`git diff --stat` before and after) are non-runtime and carry no contract surface (sad §6 coverage table).
