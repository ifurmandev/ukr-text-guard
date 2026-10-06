# Changelog — shared-detector

## shared-detector — one source for the shared detector files, copied into plugins by script, with a divergence check

**What:** the five files that the three text plugins share (`scripts/analyze.py` and four reference files) now have one source in `shared/`. `python tools/shared_sync.py sync` copies them into each plugin named in `shared/carry.json`; `check` fails when a copy differs from the source, is missing, or when a plugin holds an unlisted shared file. The check runs on demand, at the start of `bash evals/run.sh` (the eval stops before any sample, exit 3) and before every commit through `.githooks/pre-commit`, which reads the Git index, not the working folder. Copies are compared byte for byte, so a line-ending or invisible-mark difference counts as divergence. The sync never deletes a file and writes only inside a plugin folder.

**Why:** each installed plugin is a copy of its own folder, so the detector was kept as three hand-edited copies that could drift. See [spec](spec.md) §1–§2, [ADR-0001](adr/0001-read-staged-content-from-the-git-index.md) (the commit check judges the staged content), [ADR-0002](adr/0002-ship-the-hook-in-githooks-with-core-hookspath.md) (the hook ships in `.githooks/`) and [ADR-0003](adr/0003-mirror-in-skill-paths-under-shared-with-a-json-carry-list.md) (shared source mirrors in-skill paths, with a JSON carry list). The CLI is described in [cli.md](contracts/cli.md).

**How to use:** edit detection logic or a rule list only in `shared/`, then run `python tools/shared_sync.py sync`. Run `python tools/shared_sync.py check` to compare without writing. Exit codes: 0 passed, 3 divergence, 4 the check could not run. One-time setup per clone for the commit check: `git config core.hooksPath .githooks`; without it only `check` and `bash evals/run.sh` protect. A conscious bypass is `git commit --no-verify`.

**Operational notes:**
- Migration: <!-- none -->
- Feature flag / config: one-time `git config core.hooksPath .githooks` per clone (it replaces the clone's own `.git/hooks`). `.gitattributes` pins `eol=lf` for `shared/` and the plugin copies.
- Rollback: revert the PR. The first sync rewrote no plugin file (the copies already equalled the source), so plugin folders are unchanged before and after.

**Acceptance criteria delivered:** AC-01 to AC-14, including AC-03b/03c and AC-08b. Two review findings stay deferred in spec §8: an empty plugin folder reads as missing for the working-tree reader, and a CRLF source is reported as divergence of every copy rather than as a source line-ending problem (due 2026-10-19).
