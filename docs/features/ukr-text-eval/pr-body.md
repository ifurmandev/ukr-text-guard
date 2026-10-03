## Summary

Adds `evals/run_eval.py` (and a thin `run.sh`): a check that measures the detector against expected score bands fixed before the run and ends with exit code 0 or 1. Spec: [spec.md](docs/features/ukr-text-eval/spec.md). No detector rule, weight or threshold changes.

## Acceptance criteria

- AC-01, AC-02 — report lists every sample; high-level AI count is informational ✓
- AC-03, AC-04, AC-05 — false alarm and miss fail the run; drift only warns ✓
- AC-06, AC-07, AC-13, AC-14 — known-gap never fails a run, is always listed, only valid on AI samples and existing names ✓
- AC-08, AC-19 — short evidence marked inconclusive; notes never change the outcome ✓
- AC-09, AC-10 — analyzer failure fails closed; samples are independent ✓
- AC-11, AC-18 — per-plugin detector copy, missing copy fails ✓
- AC-12, AC-15, AC-17 — unclassified and empty categories fail; non-text items ignored and listed ✓
- AC-16 — outcome readable from the exit code alone ✓

## Design

- Spec: `docs/features/ukr-text-eval/spec.md`
- Architecture: `docs/features/ukr-text-eval/sad.md`
- Decisions: `docs/features/ukr-text-eval/adr/` (0001 known-gap list file, 0002 exit code only)
- CLI contract: `docs/features/ukr-text-eval/contracts/cli.md`
- Changelog: `docs/features/ukr-text-eval/changelog.md`
- Review: four rounds, final verdict PASS (`docs/features/ukr-text-eval/_review/`)

## Tasks (SDD-Task trailers)

- b624e60 pure judging function and band constants
- e577d36 discover and classify sample items
- d0ba343 known-gap list, first entry seeded
- c4cd8eb analyse one sample in a fresh process, fail closed
- 46bb415 report, evidence summary, outcome decision
- 740fd15 CLI entry point, detector copy lookup, exit code
- e588829 `run.sh` delegate
- e6a83b1 independence and repeatability on the real analyzer
- Follow-up fixes and review rounds: e513f6d, 6144761, fb03efa and the docs commits

## Verification

- Unit: `python -m unittest discover -s evals/tests` — 74 tests OK
- Lint + vet: `py_compile` clean (the repo has no linter configured)
- Ran the feature (real runs, bands/inputs broken in a scratch copy of the repo): AC-03 a human sample holding AI text → `false alarm: human-fake index 58`, exit 1; AC-05 an AI sample holding human text → `miss: ai-fake index 7`, exit 1; AC-12/17 stray `notes.txt` → unclassified error, `readme.md` and `sub/` listed as ignored, exit 1; AC-13/14 known-gap on a human sample and on a missing name → two errors, exit 1; AC-18 `--plugin ukr-text-bogus` → "no detector copy exists", exit 1; AC-11 `--plugin ukr-text-detector` → header names it, passed, exit 0. Unmodified repo: `result: passed`, exit 0.
- Not verified here: `run.sh` under a machine with no Python (covered by unit tests only).

## Operational notes

- Migration: none.
- Feature flag / config: none.
- Rollback: revert the merge; only `evals/` and docs are added.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
