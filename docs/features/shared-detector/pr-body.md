## Summary

Keeps one source of the five shared detector files in `shared/`, copies them into the three text plugins with `tools/shared_sync.py sync`, and fails a check when a copy diverges: on demand, at the start of `evals/run.sh` and before every commit (`.githooks/pre-commit`, reading the Git index). Plugin folders are unchanged by the step. [spec](docs/features/shared-detector/spec.md) · [changelog](docs/features/shared-detector/changelog.md)

## Acceptance criteria

- AC-01, AC-02 — sync rewrites or creates the copies, and says nothing was rewritten when they are equal ✓
- AC-03, AC-03b, AC-03c — a wrong carry-list entry stops the sync before any write; an unlisted file is left in place and reported ✓
- AC-04, AC-05, AC-06, AC-12 — check passes with a count, or names each differing, missing, unlisted copy; byte-exact, so CRLF counts ✓
- AC-07 — `evals/run.sh` stops on divergence with exit 3, before any sample ✓
- AC-08, AC-08b — pre-commit judges the staged content and refuses when the check cannot run ✓
- AC-09, AC-11 — README and architecture map name `shared/` as the place to edit and the one-time setup ✓
- AC-10 — the sync touches nothing outside the carried plugin copies ✓
- AC-13, AC-14 — eval passes on the synced copies; `git diff main..HEAD -- plugins` is empty ✓

## Design

- Spec: `docs/features/shared-detector/spec.md`
- Architecture: `docs/features/shared-detector/sad.md`
- Decisions: `docs/features/shared-detector/adr/` (0001 staged content from the index, 0002 hook in `.githooks`, 0003 carry list)
- CLI contract: `docs/features/shared-detector/contracts/cli.md`
- Review: `docs/features/shared-detector/_review/` (r4: PASS)

## Tasks (SDD-Task trailers)

`git log --grep SDD-Task main..HEAD` lists the per-task commits (seed `shared/`, plan core, check, sync, staged reader, pre-commit hook, `run.sh` gate, and fixes from review).

## Verification

- Unit: `tools/tests` 76 tests OK (1 skipped: file symlink, no privilege on this machine); `evals/tests` 74 tests OK.
- Lint + vet: none configured in this repo.
- Ran the feature (on a scratch copy of HEAD): edited a copy → `check` exit 3 (AC-05); `run.sh` exit 3, no sample run (AC-07); `sync` rewrote it, a second `sync` said all up to date (AC-01, AC-02); CRLF copy → `shared.line_endings` (AC-12); removed copy → `shared.missing`, `sync` created it (AC-06); a commit with a diverged copy was refused, and with no Python found it was refused with «check could not run» (AC-08, AC-08b); `bash evals/run.sh` passed on the synced tree (AC-13).
- Deferred: a real file symlink on a plugin folder (needs privilege); covered by the junction variants and stdlib behaviour.

## Operational notes

- Migration: none.
- Config: one-time `git config core.hooksPath .githooks` per clone.
- Rollback: revert the PR; plugin folders are unchanged.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
