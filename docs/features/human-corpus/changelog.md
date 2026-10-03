# Changelog — human-corpus

## Added

- Sources register `evals/samples/SOURCES.md`: rules, selection rule, entry and refusal templates, review checklist, and one entry per human sample.
- Three human samples from three authors, each registered before its file: `human-franko-miy-zlochyn` (248 words), `human-kotsiubynskyi-dorohoiu-tsinoiu` (173 words), `human-verkhovna-rada-konstytutsiia` (152 words).

## Changed

- README eval table and caption refreshed from `docs/features/human-corpus/eval-report.txt` (run of 2026-10-03, result passed): 11 samples, 3 human and 8 AI; 3 of 3 human samples reach 150 words; indexes 10, 11 and 19.

## Removed

- `human-business-letter` and `human-story`, removed because their length is below 150 words (67 and 101 words by the analyzer's count), not because of their indexes. Their earlier indexes (0 and 7) are no longer part of the baseline.

## Known limitations

- Covered genres: fiction (two stories by classics who died in 1913 and 1916) and legal documents (the opening of the 1996 Constitution of Ukraine). Not covered: business letters and mail, articles and blogs, modern informal prose and informal style. The set holds classic and official texts only, so it does not show the detector safe for other kinds of modern text.
- `human-verkhovna-rada-konstytutsiia` has index 19, above the drift mark of 15 and within the human band of 25.
- No text by the plugin author is in the set yet: the first batch had no candidate with a dated original and no third-party personal data (recorded in the register).
