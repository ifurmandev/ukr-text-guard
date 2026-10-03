# Changelog — readme-eval-table

## readme-eval-table — the README shows what the eval expects and what it measured

**What:** the sample table in the project README is now an eval table. Each of the 10 samples has its category, expected band (25 or below for human, 26 or above for AI), known-gap status, the index of the last run and the result of the row. A caption names the plugin copy measured (`ukr-text-guard`) and the run date (2026-10-03). A note beside the table says that 0 of 2 human samples reach 150 words, so the human result is inconclusive, and points to the «Чесна межа» section: the index is a heuristic, not proof of authorship. The glossary has a new term, «Eval table».

**Why:** a text author could not tell whether an index of 29 or 9 was good or bad, or that one AI sample is a tracked known-gap. See [spec](spec.md) §1–§2. The table is maintained by hand from one eval report, because no roadmap step automates it yet — [ADR-0001](adr/0001-maintain-the-eval-table-by-hand-from-one-report.md).

**How to use:** nothing to run. To refresh the table later, run `bash evals/run.sh`, check that the run finished without a run-level failure (AC-09b), and map each row of the report to the six result values in spec AC-08.

**Operational notes:**
- Migration: <!-- none -->
- Feature flag / config: <!-- none -->
- Rollback: revert the PR; the change is README.md and CONTEXT.md only, no code.

**Acceptance criteria delivered:** AC-01 (rows, counts), AC-02 (bands), AC-03 (known-gap row), AC-05 (short human evidence stated), AC-06 (index is not proof), AC-08 (table equals the report), AC-09 (nothing excused without the flag), AC-09b (run gate), AC-10 (caption: plugin and date). AC-04, AC-05b and AC-07 are rules for later refreshes and have no trigger in this run.
