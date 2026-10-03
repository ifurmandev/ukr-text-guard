---
status: Living
updated_at: "2026-10-03"
---

# Domain Context — ukr-text-guard

<!--
CONTEXT.md is the domain glossary — not a spec and not a scratch pad. NO implementation
detail here (no datastore/broker/framework names, no API contracts) — only domain words
and the boundaries between them. Implementation choices live in the SAD and ADRs; behaviour
lives in spec.md.
-->

## Glossary

- Bypass sample — an AI text deliberately written or reworked to look human and avoid detection. NOT a known-gap: a bypass sample is a kind of text, while known-gap is the flag that excuses a sample the detector misses.
- Expected band — the range of index a sample of its category must fall into, set before a run. NOT the observed index, which is only what the detector produced.
- False alarm — a human sample that received an index above the human band. NOT a miss (an AI text without a high index).
- Index — the score from 0 to 100 the detector gives a text; the higher, the more signs of AI writing. NOT the probability that an AI wrote the text.
- Known-gap — a flag the plugin author puts on an AI sample that the detector is known to miss; the sample is tracked and never fails a run. NOT a category of its own and NOT a failing check; it can never be put on a human sample.
- Ordinary AI sample — an AI sample that has no known-gap flag and must therefore reach the AI band. NOT a bypass sample (a bypass sample may or may not be flagged known-gap).
- Plugin author — the person who maintains the marketplace plugins and runs the quality check. NOT a text author.
- Reliability — the analyzer's own rating of how far the index can be trusted for a text of that length. NOT the accuracy of the detector.
- Sample — one text file in the check set, labelled either human or AI. NOT a document a text author is checking.
- Text author — the person who installs the plugins and checks or edits their own Ukrainian texts. NOT a plugin author.
