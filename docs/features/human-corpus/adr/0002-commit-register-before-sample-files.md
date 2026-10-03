---
status: Accepted
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-03"
feature_size: "S"
ticket: "N/A"
---

# 0002 — Commit each candidate to the register before its sample file

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Ihor Furman, Claude (design stage, easy depth)

## Context

The promise of this step is that the choice of human texts cannot follow the scores (spec AC-01, AC-06). The eval analyses every `human-*.txt` in the sample folder, so a file that lands in the folder is scored at once, and «registered before analysed» cannot be added after the fact. The order in which things were recorded is the only evidence the plugin author can leave for a later reader.

## Decision drivers

- A false alarm must stay visible and the set must not be shaped by the scores (spec §1, §3, §6.1 abuse case «choosing texts after seeing their scores»).
- No new executable code in this step (spec §6.1), so the evidence cannot be a script check.
- Candidate fragments must be measurable for length before registration without revealing the index (spec §6: 150 to 600 words).

## Considered options

1. **Two commits: register, then samples** — the first commit holds `SOURCES.md` with every candidate, its fragment borders and a blind word count; a later commit adds the `human-*.txt` files; the review checks that the register commit precedes the sample commit in `git log`.
2. **Two commits plus a SHA-256 of the fragment** — as option 1, and each register entry also stores the SHA-256 of the fragment as registered, so a later edit or border shift is visible mechanically.

## Decision outcome

**Chosen:** Option 1. The commit order is the evidence; the change log required by AC-08 already records every permitted edit, so a hash would duplicate it, and a hash taken over text with different line ends on Windows and Linux adds a failure mode of its own. Neither option proves that the analyzer was never run locally on a candidate, so the length is measured with the analyzer's word counter only (no `analyze()` call) and the remaining gap is carried as a named risk in SAD §11.

## Consequences

**Positive**
- Evidence costs nothing extra: git already records the order.
- The blind word count lets a candidate be refused for length (above 600 words) before any index exists.

**Negative**
- The evidence is weak against deliberate history rewriting or a local analyzer run; it rests on the plugin author's discipline and on the review checklist.
- At least two commits are needed for the first batch of samples, so the work cannot be one commit.

**Neutral**
- A later change to the human set repeats the pattern: register entry first, file second. Adding the SHA-256 later is possible without rewriting history.

## Links

- Spec: [[../spec.md]] (AC-01, AC-06, AC-08, §6.1)
- SAD: [[../sad.md]] §4, §11
- Related ADR: [[0001-keep-sources-register-as-markdown-beside-samples]]
