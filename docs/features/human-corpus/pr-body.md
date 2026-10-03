## Summary

Grows the human side of the eval from two short samples to three samples of 150+ words from three authors, with a sources register fixed before the files, and refreshes the README table and its coverage note. Spec: [spec](docs/features/human-corpus/spec.md).

## Acceptance criteria

- AC-01 — every sample matches a register entry made earlier (git order 0e574fb → 60780f0 → 715b94f) ✓
- AC-02 — register holds author, genre, source, basis, date, borders and change log per sample ✓
- AC-03 — report: 3 of 3 human samples at 150+ words, 3 authors, no inconclusive mark ✓
- AC-04 — no false alarm in this run; the rule is untouched (drift note on index 19 stays visible) ✓
- AC-05, AC-07 — own-text candidate refused and recorded; only pre-2023 texts used ✓
- AC-06, AC-08 — removals justified by length only; no edits to suit the detector ✓
- AC-09 — `human-business-letter` and `human-story` gone from report and README; changelog states the baseline change ✓
- AC-10, AC-11 — README rows, counts and caption match the report; covered and uncovered genres named ✓
- AC-12 — covered by the existing inconclusive-mark logic; not triggered (all samples ≥150 words) ✓

## Design

- Spec: `docs/features/human-corpus/spec.md`
- Architecture: `docs/features/human-corpus/sad.md`
- Decisions: `docs/features/human-corpus/adr/` (0001 register as markdown, 0002 register before samples)
- Review: `docs/features/human-corpus/_review/` (round 2: PASS)

## Tasks (SDD-Task trailers)

- 0e574fb add sources register skeleton
- 60780f0 register first batch of candidates
- 715b94f add human samples, remove two short ones
- 77598e8 save first eval report
- 1899522 refresh README eval table and caption
- 196d015 changelog note on the removed baseline

## Verification

- Unit: 74 tests OK
- Integration: `bash evals/run.sh` exit 0, `result: passed`, output equals the saved report apart from the duration line
- Lint + vet: none configured in the repo
- Ran the feature: eval run on all 11 samples; human indexes 10, 11, 19, all ≤ 25; README table checked row by row against the output

## Operational notes

- Migration: none.
- Feature flag / config: none. Detector, runner and plugins untouched.
- Note: the earlier indexes of the removed samples (0 and 7) are no longer part of the baseline.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
