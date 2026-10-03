---
status: Draft
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-03"
feature_size: "S"
---

# Spec — ukr-text-eval

> **Glossary:** [CONTEXT](../../../CONTEXT.md)
> **Reference module / docs / channels used:** None — only the interview, `docs/idea-brief.md`, `docs/roadmap.md`, `docs/architecture-map.md` and the CONTEXT glossary; the analyzer code was read only to verify facts.

## 1. Context

The detector gives a Ukrainian text an index from 0 to 100, but nobody can show that it behaves correctly. Today's check prints one line per sample and asserts nothing, and the project README lists observed indexes, not expectations. The check set has 10 samples (2 human, 8 AI); the two human samples are 101 and 67 words long (analyzer count), below the 150 words at which the analyzer rates its statistics as reliable. The plugin author cannot prove the detector works, and a text author may be wrongly flagged as having used AI without anyone noticing.

There is no external trigger; the motive is internal. The next roadmap steps — keeping the plugin copies in sync and adding a quiet hook — both need a pass/fail signal first, so measuring comes before changing.

The committed approach is to measure the detector against expected bands per category, set before the run: a human sample must stay at 25 or below (with a warning above 15), an ordinary AI sample must reach 26 or above (and a count reaching 51 or above is reported for information only). Known-gap is a flag, not a third category, and only an AI sample can carry it: the first run flags the one sample that imitates human writing, ai-prompted-human-style (index 9; ai-engineered-humanity, index 29, already reaches the AI band and stays an ordinary AI sample, decided by the plugin author during sequences, 2026-10-03); a flagged sample never fails a run and only warns when its index reaches the AI band of 26, meaning the gap may be closed. Any failure outside known-gap fails the run, and the outcome of a run can be acted on automatically by the next step without reading the report. Three guardrails are added without touching detector rules: every sample reports its word count and reliability, and the human conclusion is marked inconclusive when evidence is short; an analyzer failure or empty result counts as a failure and each sample is analysed independently of the others; and the same set can be run against any of the three plugins' detector copies, one copy per run. Rationale: no comparable tool found combines bands declared before the run, a separate false-alarm report and tracked known-gap samples; the sharpest failure found was that 101- and 67-word human samples exercise a detector with most of its rules switched off, so a green result would prove little; and the success criterion from the interview is that honest human texts never look suspicious.

Sources: `docs/idea-brief.md` §5–§7, `docs/roadmap.md` step 1, and the analyzer's own level boundaries (low up to 25). The known-gap warning line is the lower bound of the AI band, not a number derived from observed indexes, so it too is fixed before the run. Decision overrides: none.

## 2. Goals

- The plugin author can tell in one run whether honest human texts stay out of the suspicious zone.
- A failing run names the sample and the reason; known-gap samples never block a run but show when a gap may have closed.
- In every run, the result states how far its evidence reaches: how many human samples reach the analyzer's reliability boundary of 150 words.

## 3. Non-goals

- Changing detector rules, weights or thresholds — a separate tuning job, outside this iteration (`docs/idea-brief.md` §5).
- Making bypass samples pass/fail — they stay known-gap and are tracked, not required.
- Growing the human sample set across genres and authors — that is the next roadmap step.
- Publishing the table in the README — a separate roadmap step.
- Fixing false alarms caused by a byte-order mark or invisible characters in saved files — that is a rule change; it is recorded as a known limitation.
- Exact-score equality between plugin copies — the check uses bands only; proving that copies are identical belongs to the sync step's own divergence check.

## 4. User stories

### US-01: Run the check

**As a** plugin author
**I want** to run all samples against expected bands and get a pass/fail report
**So that** I know whether the detector works.

### US-02: See false alarms

**As a** plugin author
**I want** human samples above their band listed separately
**So that** I can see when the detector accuses a person.

### US-03: Track known-gaps

**As a** plugin author
**I want** bypass samples kept as known-gap, and a warning when one reaches the AI band
**So that** I notice when a gap closes without a failing run.

### US-04: Know the evidence

**As a** plugin author
**I want** each sample's word count and reliability, and an inconclusive mark on the human conclusion when samples are short
**So that** I do not take a green run on very short texts as proof.

### US-05: Trust the tool

**As a** plugin author
**I want** an analyzer failure counted as a failure, never as a low index
**So that** a broken detector copy cannot look like a clean human text.

### US-06: Check every copy

**As a** plugin author
**I want** to run the same set against each plugin's detector copy
**So that** I can rely on the result after the copies are synchronised.

### US-07: Add a sample safely

**As a** plugin author
**I want** a new sample judged by its category band, and an unclassifiable sample reported rather than skipped
**So that** no sample silently drops out of the check.

### US-08: Not be accused

**As a** text author
**I want** the check to fail whenever a human sample is labelled suspicious
**So that** the detector is not shipped with false accusations of people.

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** a plugin author has samples of both categories and every sample falls within its expected band
**When** the plugin author runs the check
**Then** the report lists each sample with its category and index, states that all samples passed, and the run is reported as successful

### AC-02 (US-01) — happy path

**Given** the ordinary AI samples have indexes of various levels
**When** the plugin author runs the check
**Then** the report states how many ordinary AI samples reach the high level (51 or more) for information, and this count never changes whether the run passes

### AC-03 (US-02, US-08) — error

**Given** a human sample receives an index above the human band of 25
**When** the plugin author runs the check
**Then** the report lists that sample separately as a false alarm with its name and index, and the run is reported as failed

### AC-04 (US-02) — happy path

**Given** a human sample receives an index above 15 and within the human band of 25
**When** the plugin author runs the check
**Then** the report warns about drift and names the sample, and the run still passes

### AC-05 (US-01) — error

**Given** an ordinary AI sample receives an index below the AI band of 26
**When** the plugin author runs the check
**Then** the report lists that sample as a miss with its name and index, and the run is reported as failed

### AC-06 (US-03) — domain invariant: a known-gap sample never fails a run

**Given** a known-gap sample receives an index of 26 or above
**When** the plugin author runs the check
**Then** the report warns that the gap may be closed and the label should be reviewed, and the run is not failed because of that sample

### AC-07 (US-03) — authorization: only an explicit entry by the plugin author excuses a sample

**Given** a sample without an explicit known-gap entry by the plugin author falls outside its band
**When** the plugin author runs the check
**Then** the report does not excuse it, and the report lists every known-gap sample so each excused sample is visible

### AC-08 (US-04) — domain invariant: short evidence is never stated as conclusive

**Given** any set of samples
**When** the plugin author runs the check
**Then** the report shows each sample's word count and reliability, both taken from the analyzer's own count and rating, states how many human samples reach 150 words out of how many, and marks the human conclusion as inconclusive whenever fewer than all of them do

### AC-09 (US-05) — error

**Given** the analyzer crashes for a sample, returns an empty or unreadable result, leaves out the index or the reliability, returns an index outside 0 to 100, or gives no result within 10 seconds
**When** the plugin author runs the check
**Then** that sample is reported as an analyzer failure with the reason, counted as failed, and never shown as a low index

### AC-10 (US-05) — domain invariant: samples do not affect each other

**Given** the same samples
**When** the plugin author runs them alone or together with others in any order
**Then** each sample receives the same index and the same verdict

### AC-11 (US-06) — cross-context

**Given** each of the three text plugins (ukr-text-guard, ukr-text-detector, ukr-text-editor) carries its own detector copy
**When** the plugin author runs the check against one chosen plugin's copy, or names none
**Then** the report names the plugin whose copy was used (ukr-text-guard when none is named), the results come only from that copy, and a failing copy fails only its own run

### AC-12 (US-07) — error

**Given** a plain text file in the sample folder whose name does not start with human- or ai-
**When** the plugin author runs the check
**Then** the report lists it as unclassified, the run is reported as failed, and the report gives the number of samples per category so a missing sample is visible

### AC-13 (US-03, US-08) — domain invariant: known-gap applies only to AI samples

**Given** the plugin author has put a known-gap flag on a human sample
**When** the plugin author runs the check
**Then** the report lists that flag as an error naming the sample, the sample is judged against the human band as usual, and the run is reported as failed

### AC-14 (US-03) — error

**Given** a known-gap flag names a sample that does not exist
**When** the plugin author runs the check
**Then** the report lists the flag as an error naming it, and the run is reported as failed

### AC-15 (US-07) — error

**Given** there are no samples at all, or no samples in the human category, or none in the AI category
**When** the plugin author runs the check
**Then** the report names the missing category and the run is reported as failed

### AC-16 (US-01, US-06) — domain invariant: the outcome is usable without reading the report

**Given** any run of the check
**When** the run ends
**Then** its outcome, success or failure, can be acted on automatically by the next step without reading the report

### AC-17 (US-07) — happy path

**Given** the sample folder also contains files that are not plain text files, or items inside subfolders
**When** the plugin author runs the check
**Then** the report lists them as ignored and they do not change the outcome

### AC-18 (US-06) — error

**Given** the plugin author names a plugin that has no detector copy
**When** the plugin author runs the check
**Then** the report says that no detector copy exists for that plugin, and the run is reported as failed

### AC-19 (US-04) — domain invariant: notes never change the outcome

**Given** a run in which no sample fails but the human conclusion is inconclusive, or a drift warning or a gap-may-be-closed warning is shown
**When** the run ends
**Then** the run is reported as successful, because inconclusive marks and warnings are notes and never change whether a run passes

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Run time of one run of one detector copy over up to 50 samples, on the plugin author's machine | ≤ 60 s | duration printed in the report |
| Time limit per sample before it counts as an analyzer failure | 10 s | the report names any sample that exceeded it |
| Repeatability | two consecutive runs on the same inputs give identical indexes and verdicts, 100% | difference between two consecutive reports |
| Independence of samples | each sample's verdict is identical when it is run alone, together with the others, and in reverse order, 100% | comparison of the three runs before release |
| Cost of adding a sample of a known category | 0 edits to expected bands | the band definition is unchanged in the commit that adds the sample |
| Platforms | identical verdicts in the plugin author's Windows shell and in a POSIX-compatible shell on the same machine, 2 of 2; a separate Linux or macOS host is not required | one run in each before release |
| Report completeness | 100% of sample files appear in the report, as classified, unclassified or ignored | per-category counts plus ignored items sum to the number of items in the folder |

## 6.1 Security / privacy

- **Data classification:** internal; the repository is public, so committed samples become public.
- **Personal data touched:** none today; texts by other authors may contain personal data and need their permission before they are committed.
- **AuthZ/AuthN impact:** none — a local run with no accounts and no network.
- **Abuse cases:**
  - A crafted sample that makes the analyzer fail: counted as a failure (AC-09).
  - A sample in an unexpected encoding or with hidden characters: reported, never silently dropped (AC-09, AC-12).
  - A failing sample relabelled known-gap to turn the run green: stays visible in the known-gap list (AC-07); a human sample carrying the flag is an error (AC-13).
- **Security review:** N/A — a local script with no network and no authorization boundary.

## 7. Metrics / KPIs

- **False alarms named** — baseline: 0% of runs (no report exists), target: 100% of runs name every false alarm, from the first run of this step.
- **Evidence disclosed** — baseline: 0% of runs, target: 100% of runs state how many human samples reach 150 words, from the first run.
- **Silent drops** — baseline: unknown, no count exists today (measurement plan: per-category counts plus ignored items must sum to the number of items in the folder, AC-12 and AC-17), target: 0 per run.
- **Time to a verdict** — baseline: not possible, ten unasserted lines to read by hand, target: ≤ 60 s in one command, on completion of this step.

## 8. Open questions

- [x] Is 150 words the right threshold for a human sample to count as long enough, or should it be 300, where most detector rules switch on? Default now: 150 (the analyzer's own reliability boundary). — owner: plugin author, due: before `sdd:design` — resolved in design (2026-10-03) at the default 150, kept as one named constant (`sad.md` §8 Configuration)
- [ ] Where do human texts by other authors come from, and with whose permission? Default now: none are added in this step. — owner: plugin author, due: before the broader human set step
- [ ] Should the known limitation about byte-order marks and invisible characters be printed in the report, or fixed in the analyzer in the next iteration? Default now: printed only for samples that contain such characters, saying that a high index may come from the file rather than the text, and not fixed. — owner: plugin author, due: before the next detector iteration
