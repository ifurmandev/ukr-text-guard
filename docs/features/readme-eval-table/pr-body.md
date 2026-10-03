## Summary

Replaces the README sample table with an eval table: per sample the category, expected band, known-gap status, index of the last run and result, with a caption (plugin copy and run date) and a note that the human evidence is inconclusive (0 of 2 human samples reach 150 words). Adds the glossary term «Eval table». Documentation only. [Spec](docs/features/readme-eval-table/spec.md).

## Acceptance criteria

- AC-01 — all 10 samples listed with category, band, known-gap status, index, result; counts «2 людських і 8 ШІ» ✓
- AC-02 — bands 25 or below (human) and 26 or above (AI) ✓
- AC-03 — `ai-prompted-human-style` marked as known-gap, index 9 visible ✓
- AC-05 — note: 0 of 2 human samples reach 150 words, result inconclusive, not proof ✓
- AC-06 — the index is a heuristic, pointer to «Чесна межа» ✓
- AC-08 — every cell equals the report below, zero differences ✓
- AC-09 / AC-09b — no sample excused without the flag; table taken from a run without a run-level failure ✓
- AC-10 — caption names `ukr-text-guard` and 3 жовтня 2026 року ✓
- AC-04, AC-05b, AC-07 — refresh rules, no trigger in this run

## Design

- Spec: `docs/features/readme-eval-table/spec.md`
- Architecture: `docs/features/readme-eval-table/sad.md`
- Decisions: `docs/features/readme-eval-table/adr/0001-maintain-the-eval-table-by-hand-from-one-report.md`
- Review: `docs/features/readme-eval-table/_review/review-2026-10-03.md` (PASS)

## Tasks (SDD-Task trailers)

T1–T5 are documentation edits; commits: c831112 (rows), 4238f80 (result column), c8e4780 (caption, note, pointer), 8f3d89e (glossary), a9eab78 (note wording after review), d5b9a10 (spec, tasks, review record).

## Verification

- Eval report of the run named in the caption (`bash evals/run.sh`, 2026-10-03, exit 0), pasted for the Accuracy check (spec §6):

```
plugin: ukr-text-guard
ai-chat-residue-placeholders             AI            index 70   words 43   reliability низька (текст закороткий)   passed
ai-cliche                                AI            index 58   words 113   reliability низька (текст закороткий)   passed
ai-engineered-humanity                   AI            index 29   words 107   reliability низька (текст закороткий)   passed
ai-homoglyph-obfuscated                  AI            index 83   words 113   reliability низька (текст закороткий)   passed
ai-prompted-human-style                  known-gap AI  index 9   words 226   reliability середня   passed
ai-website-stages-2010-2015              AI            index 70   words 755   reliability прийнятна   passed
ai-website-stages-generic                AI            index 44   words 348   reliability середня   passed
ai-zero-width-obfuscated                 AI            index 83   words 113   reliability низька (текст закороткий)   passed
human-business-letter                    human         index 0   words 67   reliability низька (текст закороткий)   passed
human-story                              human         index 7   words 101   reliability низька (текст закороткий)   passed

known-gap samples (excused by evals/known-gaps.txt):
  known-gap: ai-prompted-human-style  # imitates human writing, index 9 on the first run

notes:
  hidden characters: ai-zero-width-obfuscated has a byte-order mark or invisible characters, a high index may come from the file rather than the text
  human conclusion inconclusive: only 0 of 2 human samples reach 150 words

summary: 2 human, 8 AI, 0 unclassified, 0 ignored, 10 of 10 items
result: passed
```

- Unit: 74 tests in `evals/tests` OK (nothing in code changed).
- Lint + vet: N/A, no code files.
- Ran the feature: ran the eval and compared all 10 rows, counts, bands, caption and the `#чесна-межа` anchor with the table; an independent reviewer did the same, 0 differences. The rendered README on the repository host is not opened from here; open it before merge (1 table, 6 columns).

## Operational notes

- Migration: none.
- Feature flag / config: none.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
