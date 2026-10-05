# Acceptance run — shared-detector

Run on 2026-10-05 on the plugin author's Windows machine (Git Bash), branch `shared-detector`, after tasks T1–T8 were committed. Task T9 records results and changes no code.

## AC-13 — eval parity on all three analyzer copies

Command: `bash evals/run.sh --plugin <name>` for `ukr-text-guard`, `ukr-text-detector`, `ukr-text-editor`. Each run first printed `checked 12 files in 3 plugins` / `result: passed`, then ended with exit code 0.

| Sample | Index (all three copies) | Row result | README table index |
|---|---|---|---|
| ai-chat-residue-placeholders | 70 | passed | 70 |
| ai-cliche | 58 | passed | 58 |
| ai-engineered-humanity | 29 | passed | 29 |
| ai-homoglyph-obfuscated | 83 | passed | 83 |
| ai-prompted-human-style | 9 | passed (known gap) | 9 |
| ai-website-stages-2010-2015 | 70 | passed | 70 |
| ai-website-stages-generic | 44 | passed | 44 |
| ai-zero-width-obfuscated | 83 | passed | 83 |
| human-franko-miy-zlochyn | 10 | passed | 10 |
| human-kotsiubynskyi-dorohoiu-tsinoiu | 11 | passed | 11 |
| human-verkhovna-rada-konstytutsiia | 19 | passed | 19 |

The output of the detector and editor runs equals the guard run line for line, apart from the `plugin:` line and the duration. The 11 indices equal the committed README table. **Met.**

## AC-14 — plugin folders unchanged

`git diff --stat e859de7..HEAD -- plugins evals/run_eval.py evals/tests` (e859de7 is the last commit before the step): empty. No file was added to, removed from or moved in any plugin folder, so every file a skill description tells Claude to read is on the same path as before. **Met.**

## Spec section 6 NFRs

| Aspect | Target | Measured | Result |
|---|---|---|---|
| Duration of `check` | ≤ 2 s | 0.12 s (`python`), 0.17 s (`py`); `check --staged` 0.77 s | met |
| Duration of `sync` | ≤ 2 s | 0.14 s (`python`), 0.14 s (`py`) | met |
| Idempotence | first and second sync on current files rewrite 0 files | both runs printed `all copies are up to date`, `git status` shows no change under `plugins/` or `shared/` | met |
| Unchanged eval | 0 changed lines in `evals/run_eval.py` and `evals/tests/`; 74 of 74 tests pass | empty diff; `python -m unittest discover -s evals/tests` → 74 tests OK | met |
| Completeness of detection | each of the 4 divergence kinds caught by at least 1 test | `BuildPlanTest` covers differing, missing, unlisted, line endings only, plus invisible mark | met |
| Environment | each present interpreter works, 0 imports outside the standard library | `python` and `py` (3.12.10) work; `python3` is not present (the Microsoft Store stub does not run), so it is marked not present, not a failure; imports are `json`, `os`, `subprocess`, `sys`, `dataclasses`, `typing` | met |

New tests: `python -m unittest discover -s tools/tests` → 71 tests OK (plan core, check, sync, staged reader on a real temporary Git repository, hook, `run.sh`).

## Not verified here

- Python 3.8 compatibility was not run (only 3.12.10 is installed); the code avoids `match`, `tomllib` and 3.9+ typing syntax.
- `python3` was not present on this machine, so the entry points were not run with it.
