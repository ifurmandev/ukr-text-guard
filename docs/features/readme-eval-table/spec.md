---
status: Approved
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-03"
feature_size: "XS"
---

# Spec — readme-eval-table

> **Glossary:** [CONTEXT](../../../CONTEXT.md)
> **Reference module / docs / channels used:** None — only the interview, `docs/idea-brief.md`, `docs/roadmap.md` step 2, the CONTEXT glossary and the project README; the eval runner (`evals/run_eval.py`) and one run of it were read only to verify facts.

## 1. Context

The project README has a table of the 10 check samples with the index each got, but it gives no expected band and does not say which sample the detector is known to miss. A text author who installs the plugins cannot tell whether an index of 29 for the engineered-humanity sample is good or bad, or whether 9 for the prompted-human-style sample is a failure or an expected gap. The facts exist: the eval step shipped on 2026-10-03 judges every sample against a band fixed before the run (human 25 or below, ordinary AI 26 or above) and tracks one sample as known-gap. They live only in the plugin author's terminal output.

There is no external trigger; the motive is internal. The idea brief (§7) asks to update the README table right after the first eval step so that users see measured quality early, and roadmap step 2 is the only step that does not wait for anything else.

The committed approach is to replace the README sample table with an eval table: one row per sample with its category, expected band, known-gap status, the index of the last run and the result of the row (passed, failed with its reason, or gap may be closed), a caption that names the plugin copy measured and the date of the run, and a note beside it that states how far the evidence reaches. In the first run both human samples are short (67 and 101 words, below the 150 words under which the analyzer marks its statistics as low («текст закороткий»)), so the human conclusion is inconclusive and the table must say so rather than read as proof. A failing sample is shown as failed with its reason, never softened. The plugin author refreshes the table by hand from the eval report; generating it and checking drift have no roadmap step yet (§3, §8).

Sources: `docs/idea-brief.md` §6–§7, `docs/roadmap.md` step 2, the shipped eval spec (`docs/features/ukr-text-eval/spec.md`). Decisions taken as defaults at easy interview depth and accepted as a batch by the plugin author on 2026-10-03: hand-maintained table, bands as the eval defines them, honest-limit note, failed samples shown as failed, ukr-text-guard copy with the run date, new table replaces the old one, README prose in Ukrainian, the term "Eval table" added to the glossary, no extra channels and no ideation analyses. Amended after the critic review, by the plugin author, on 2026-10-03: a sixth column "result" is added to the five first accepted, because the row-level outcomes need a place in the table, and the rule to refresh the table in later steps' changes is dropped from this spec, because it would bind the parallel roadmap steps 3 and 4. Decision overrides: none.

## 2. Goals

- A text author can see, per sample, what the detector is expected to do and what it did, without running anything.
- A text author can see which AI samples the detector is known to miss, and that these are tracked rather than hidden.
- The table never claims more than the run behind it shows: short human evidence and failing samples are stated, not softened.

## 3. Non-goals

- Generating the table by script or checking its drift automatically — no roadmap step covers it today (step 4 syncs the detector copies, not the README); this step is one hand-made edit.
- Changing the eval runner, the detector, the bands or the sample set — outside an XS change; growing the human set is roadmap step 3.
- Showing the other two plugin copies in the table — proving the copies identical belongs to step 4's own divergence check.
- Adding word-count or reliability columns — the report holds them and one note beside the table is enough.
- Restructuring or translating the README — only the sample table area changes: the table, its caption and the notes beside it. The `bash evals/run.sh` block stays as it is, and the one intro line of the check section may be reworded only to fit the caption.
- Showing drift warnings or hidden-character and encoding notes of the report in the table — they stay in the report; the table shows only the result of each row and the one evidence note (AC-05).
- Copying the reason the plugin author recorded for a known-gap flag into the table — the row says only that passing the band is not required (AC-03).

## 4. User stories

### US-01: See measured quality

**As a** text author
**I want** every sample listed with its expected band and the index it got
**So that** I can judge from the README how the detector behaves without running it.

### US-02: See known misses

**As a** text author
**I want** the AI samples the detector is known to miss marked as known-gap, with a sign when one stops being a miss
**So that** I know the limits of the detector and see that they are tracked, not hidden.

### US-03: Not be misled by short evidence

**As a** text author
**I want** the table to say how many human samples are long enough to count
**So that** I do not read a clean result on very short texts as proof that the detector never accuses a person.

### US-04: Keep the table honest

**As a** plugin author
**I want** to refresh the table from one eval report so that it matches the report, shows failures as failures and excuses only samples I flagged
**So that** the README never shows a broken detector as healthy.

### US-05: Know which run the table shows

**As a** plugin author
**I want** the table to name the plugin copy measured and the date of the run
**So that** a reader and I can tell how stale it is.

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** a text author opens the project README
**When** the text author reads the eval table
**Then** the table lists every sample of the check set, each with its category (human or AI), its expected band, its known-gap status, the index it got in the last run and the result of the row, and states how many samples there are per category

### AC-02 (US-01) — happy path

**Given** the eval table lists a human sample and an ordinary AI sample
**When** the text author reads their expected bands
**Then** the human sample shows a band of 25 or below and the ordinary AI sample shows a band of 26 or above, the same bands the eval judges against; a known-gap AI sample shows the AI band too (26 or above) and its exemption is stated in its result (AC-03)

### AC-03 (US-02) — happy path

**Given** the plugin author has flagged an AI sample as known-gap
**When** the text author reads that sample's row
**Then** the row is marked as known-gap, its result says that passing its band is not required, and it shows the index it got, so a low index on that sample is visible and explained rather than hidden

### AC-04 (US-02) — domain invariant: a gap that may be closed is flagged

**Given** a known-gap sample received an index of 26 or above in the last run
**When** the text author reads its row
**Then** the result of the row says the gap may be closed and the label should be reviewed, instead of showing it as an ordinary pass

### AC-05 (US-03) — domain invariant: short evidence is never stated as conclusive

**Given** fewer than all human samples reach 150 words in the last run
**When** the text author reads the eval table
**Then** a note beside the table states how many human samples reach 150 words out of how many, says the result for human texts is inconclusive, and does not present the table as proof that the detector never accuses a person

### AC-05b (US-03) — edge: all human samples long enough

**Given** every human sample reaches 150 words in the last run
**When** the text author reads the eval table
**Then** the note beside the table still states how many human samples reach 150 words out of how many, and no longer says the result for human texts is inconclusive

### AC-06 (US-01) — domain invariant: the index is not proof

**Given** a text author sees an index in the eval table
**When** the text author reads the text around the table
**Then** the README states that the index is a heuristic of signs of AI writing and not proof of authorship, by pointing to its existing section on the honest limit

### AC-07 (US-04) — error

**Given** the last run failed because a human sample is a false alarm, an ordinary AI sample is a miss, or the analyzer failed on a sample
**When** the plugin author refreshes the eval table from that run
**Then** the result of the affected row says failed with its reason (false alarm, miss or analyzer failure), the row shows its index for a false alarm and a miss and a dash for an analyzer failure (the report prints no index for that row; when the failure is an index outside 0 to 100, the number appears only in the failure reason), and the table is not worded as if every sample passed

### AC-08 (US-04) — cross-context: the table equals the eval report

**Given** the plugin author has the report of one eval run
**When** the plugin author refreshes the eval table
**Then** each row's category, known-gap status, index and result equal the report, the rows are exactly the samples the report lists, and the per-category counts (human and AI) equal the report's summary
**And** the result of a row is derived from the report as follows: the row verdict plus the report section that lists the sample, giving one of six values, shown in Ukrainian; an analyzer failure takes precedence over a known-gap flag (the report judges a failed analysis as failed even on a flagged sample), and a drift warning leaves the result «пройдено» — passed («пройдено»), failed: false alarm («провал: хибна тривога»), failed: miss («провал: пропуск»), failed: analyzer failure («провал: збій аналізатора»), known-gap («відомий пропуск, проходити смугу не обов'язково»), gap may be closed («пропуск, можливо, закрито, переглянути мітку»); the categories are shown as «людський» and «ШІ»

### AC-09 (US-04) — authorization: only the plugin author's explicit flag excuses a sample

**Given** a sample is outside its expected band and the plugin author has not flagged it as known-gap
**When** the plugin author refreshes the eval table
**Then** the row is shown as failed and not as known-gap, and a human sample is never shown as known-gap

### AC-09b (US-04) — error: a run that failed as a whole is not published

**Given** the last run failed at run level although every row passed, for example because of an unclassified sample, a wrong known-gap list, a missing category, a missing detector copy or a runner error (an error other than a failed row)
**When** the plugin author wants to refresh the eval table
**Then** the table is not refreshed from that run; the cause is fixed first and the table is taken from a run that finished without a run-level failure

### AC-10 (US-05) — happy path

**Given** the plugin author refreshed the table from a run on one detector copy
**When** the text author reads the caption of the eval table
**Then** the caption names the plugin whose detector copy was measured and the date of the run, the calendar date on which the plugin author ran the eval (the report prints none); plugin and date identify the run to the day

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Accuracy | 100% of table cells (category, known-gap status, index, result) equal the report of the run named in the caption | the plugin author pastes the report output into the pull request description and the reviewer compares the table with it before the change is merged |
| Completeness | 100% of the human and AI samples the report lists appear as rows (unclassified and ignored files are not samples; an unclassified file fails the run, AC-09b); per-category row counts equal the report's summary | compare counts before merge |
| Rendering | 1 table, 6 columns, plain markdown with 0 HTML, shown as a table on the repository host page | open the rendered README before merge |
| Language | 100% of the table headers, the cell values (category, known-gap status, result), the caption and the notes in Ukrainian, like the rest of the README; the correspondence with the English report is the mapping in AC-08 | read-through in review |
| Footprint | 2 files changed outside the docs folder (the README and the glossary file), 0 code files | diff of the change |

## 6.1 Security / privacy

- **Data classification:** public — the README is shown on a public repository.
- **Personal data touched:** none; the table shows sample names and indexes only, never the sample texts.
- **AuthZ/AuthN impact:** none — a documentation edit with no accounts and no network.
- **Abuse cases:**
  - A failing sample relabelled known-gap in the table to look healthy: the row is judged against the flag list the plugin author keeps, not against the table (AC-09).
  - A short-evidence result presented as proof: the note beside the table states the evidence limit (AC-05).
- **Security review:** N/A — one documentation table, no network and no authorization boundary.

## 7. Metrics / KPIs

- **Expected band visible** — baseline: 0 of 10 rows in the README today, target: 10 of 10 rows, on merge of this step.
- **Known-gap status visible** — baseline: 0 of 1 known-gap samples marked, target: 1 of 1 marked, on merge of this step.
- **Table equals report** — baseline: the 10 indexes match today but neither the plugin copy nor the date is named, target: 100% of cells match the run named in the caption, on merge and at every later refresh.
- **Evidence limit disclosed** — baseline: 0 notes, target: 1 note stating how many human samples reach 150 words, on merge of this step.

## 8. Open questions

- [ ] Should the runner print the table so that it is no longer edited by hand, and where should a drift check run? Default now: by hand, no check. — owner: plugin author, due: when a roadmap step for it is added (none exists today)
- [ ] Who refreshes the table when samples, the known-gap list, the bands or a detector copy change later? Default now: the plugin author, by hand, in the same change, as a habit and not as a rule. — owner: plugin author, due: before roadmap step 3
- [ ] Should a row also show the sample's word count and reliability? Default now: no, only the note beside the table. — owner: plugin author, due: roadmap step 3, when the broader human set changes how the note reads
- [ ] Should the table cover the other two plugin copies once they are synchronised? Default now: only the ukr-text-guard copy. — owner: plugin author, due: after roadmap step 4

## Test plan

Checks are run by hand by the reviewer before merge: the feature changes documentation only (0 code files, §6 Footprint), so no automated test is added.

### Levels

| Level | Scope | Strategy |
|---|---|---|
| contract | table ↔ eval report boundary | the plugin author pastes one run's report into the pull request; the reviewer compares each table cell with it using the mapping in AC-08 |
| e2e | a text author reading the rendered README | open the README as rendered on the repository host and read the table, caption and notes as a text author would |
| unit | — | <!-- N/A: no pure logic is added --> |
| integration | — | <!-- N/A: no dependency is touched --> |
| load | — | <!-- N/A: no numeric NFR to load-test --> |

### AC coverage

| AC (spec.md §5) | Test name (intent-based) | Level | Expected outcome |
|---|---|---|---|
| AC-01 happy path | every sample of the check set is a row with category, band, known-gap status, index and result, and per-category counts are stated | contract + e2e | rows and counts equal the report |
| AC-02 happy path | human band reads 25 or below, ordinary AI band reads 26 or above, known-gap AI sample shows the AI band | contract | bands equal the eval's bands |
| AC-03 happy path | known-gap row shows its index and says passing the band is not required | contract | row marked as known-gap, low index visible and explained |
| AC-04 domain invariant | known-gap sample with index 26 or above is shown as gap may be closed | contract | row says the label should be reviewed, not an ordinary pass |
| AC-05 domain invariant | note states how many human samples reach 150 words and calls the human result inconclusive | e2e | note present, no claim of proof |
| AC-05b edge | when all human samples reach 150 words the note keeps the count and drops «inconclusive» | e2e | count stays, no inconclusive wording |
| AC-06 domain invariant | text around the table points to the honest-limit section and says the index is not proof | e2e | pointer present |
| AC-07 error | failed row shows its reason and its index (a dash for an analyzer failure) | contract | table is not worded as all-passed |
| AC-08 cross-context | every cell, row set and per-category count equals the report, via the result mapping | contract | zero differences |
| AC-09 authorization | an out-of-band sample without the plugin author's flag is failed; a human sample is never known-gap | contract | no unflagged row excused |
| AC-09b error | a run that failed as a whole is not used for a refresh | contract | table taken only from a run without a run-level failure |
| AC-10 happy path | caption names the plugin copy and the run date | e2e | both present |

### Edge cases / error paths

- analyzer failure on a flagged known-gap sample → expected: shown as failed with its reason, not as known-gap.
- drift warning on a human sample → expected: result stays passed, warning not shown in the table.
- unclassified file in the sample folder → expected: no refresh until fixed (AC-09b).
- report lists no human sample reaching 150 words → expected: note says 0 of N and inconclusive.

### Test data

- Seed: one real run of the eval on the ukr-text-guard copy; its report output is the reference.
- Cleanup: none, nothing is created besides the pasted report in the pull request.

### NFR validation (load)

<!-- N/A: no numeric NFR to load-test -->

Rendering, Language and Footprint NFRs (§6) are checked in the same review: open the rendered README (1 table, 6 columns, 0 HTML), read the Ukrainian wording, and read the diff (2 files outside docs, 0 code files).

### CI placement

- No automated suite. Every check above runs in the review before merge.
