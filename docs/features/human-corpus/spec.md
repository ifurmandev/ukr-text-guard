---
status: Draft
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-03"
feature_size: "S"
---

# Spec — human-corpus

> **Glossary:** [CONTEXT](./CONTEXT.md) (feature) · [CONTEXT](../../../CONTEXT.md) (project)
> **Reference module / docs / channels used:** `README.md` (the eval table and its caption) and `evals/tests/test_run_eval.py`, read to state facts about the current set; otherwise only the interview, `docs/idea-brief.md`, `docs/roadmap.md`, `docs/features/ukr-text-eval/spec.md` and the eval runner, read to verify facts.

## 1. Context

The detector gives a Ukrainian text an index from 0 to 100, and the shipped eval checks it against bands fixed before the run: a human sample must stay at 25 or below. The human side of that check is thin. It holds two samples, both below the 150 words at which the analyzer rates its statistics as reliable, and both are probably the plugin author's own writing. So the eval marks every human conclusion as inconclusive, and the README says that 0 of 2 human samples reach 150 words. The plugin author cannot tell whether the detector wrongly flags people in general or only fails to flag one voice, and a text author reading the README cannot tell what the measured quality covers.

There is no external trigger; the motive is internal. This is step 3 of the roadmap, and step 5 (a quiet hook) takes its thresholds from the eval, so the human evidence has to be wider and honestly described before anyone sets a threshold.

The committed approach is to grow the human set with texts the plugin author may lawfully publish in a public repository: public-domain classics, official documents that fall outside copyright, and the plugin author's own texts written before 2023 without third-party data. Every human sample reaches 150 words and comes from at least three authors, at least one of them another person (neither the plugin author nor an official body), so that three authors cannot be reached with one voice and two bodies. Every candidate, with the borders of its fragment, is recorded in a sources register before the analyzer is first run on the text, and a text is never replaced because of its index, so a false alarm stays visible and the eval stays red. Rationale: the research found no verified free source of modern business mail, blogs or informal fiction with a proven pre-AI date, and only official documents are clearly outside copyright, so the plugin author's own texts fill the gap and the report and README must say plainly which genres are covered. The sharpest failure found is that formal and legal text may score above 25 with no way out, because the detector is frozen and the known-gap flag cannot be put on a human sample, and the second is choosing texts after seeing their scores, which would make the eval mirror the detector. The success criterion from the interview is at least three authors with every human sample at 150 words or more.

Sources: `docs/idea-brief.md` §6–§8, `docs/roadmap.md` step 3 and open decision D1 (closed here), the CONTEXT glossary. Decision overrides: the interview first chose «free texts only, all four genres»; research showed that this cannot be met for modern business mail and blogs, and the plugin author amended the choice to free texts plus their own pre-2023 texts, with coverage reported honestly.

## 2. Goals

- The plugin author can state in one run whether human texts from at least three authors, one of them another person, stay out of the suspicious zone, with the human conclusion no longer marked inconclusive.
- Every human sample can be traced to its author, source, basis for publication and date of writing, and the set cannot be shaped by the scores.
- A text author reading the README sees which genres and how many authors the measured quality covers, and which genres it does not cover.

## 3. Non-goals

- Changing detector rules, weights or thresholds — a separate tuning job outside this iteration (`docs/idea-brief.md` §5); every false alarm found is recorded as a known limitation.
- Changing the eval itself or making it check the sources register — this step adds data only; whether the eval should check the register is a separate decision (§8).
- Covering modern texts by other authors in business mail, blogs and informal fiction — no free source with a proven pre-AI date was found; the gap is reported, not hidden.
- Making false alarms pass or excusing them — the known-gap flag exists only for AI samples, and excusing human texts would hide the very signal step 5 needs.
- Adding AI or bypass samples — they belong to the existing set and are outside this step.
- Setting hook thresholds or claiming statistical significance — that is step 5, and a few texts only make the evidence less noisy.
- Automating the refresh of the README table — it stays a manual refresh from the report, as in the previous step.

## 4. User stories

### US-01: Record candidates first

**As a** plugin author
**I want** every candidate and the borders of its fragment recorded before the analyzer is first run on the text
**So that** the choice of texts cannot follow the scores.

### US-02: Keep the origin of each text

**As a** plugin author
**I want** each human sample to have an author, genre, source, basis for publication, date of writing with its evidence, fragment borders and a log of changes to the text in the sources register
**So that** I can later answer why the text counts as human and why it may sit in a public repository.

### US-03: Get long human evidence

**As a** plugin author
**I want** human samples of 150 words or more from at least three authors, at least one of them another person
**So that** the eval no longer marks the human conclusion as inconclusive.

### US-04: Keep false alarms visible

**As a** plugin author
**I want** a human sample the detector wrongly flags to stay in the set and show as a false alarm
**So that** the real rate of false accusations is not hidden by removing awkward texts.

### US-05: Refuse texts I may not publish

**As a** plugin author
**I want** a candidate without a nameable basis for publication refused and the refusal recorded
**So that** the public repository holds no text it has no right to hold.

### US-06: Replace the two short samples

**As a** plugin author
**I want** the two short human samples replaced by longer texts
**So that** the condition «every human sample reaches 150 words» can hold.

### US-07: Publish honest coverage

**As a** plugin author
**I want** the README table and caption to show the new set and the genres covered or not covered
**So that** the published figures match the latest report.

### US-08: Know what the figures cover

**As a** text author
**I want** to see in the README which genres and how many authors the measured quality rests on
**So that** I do not read a result for classic or official texts as proof for my own kind of text.

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** the plugin author has chosen candidates and fixed the selection rule that gives the borders of each fragment
**When** the plugin author records them in the sources register before running the analyzer on any of them
**Then** the register lists each candidate with its fragment borders, and each sample in the check set can be matched to an entry made earlier

### AC-02 (US-02) — happy path

**Given** a human sample has been added to the check set
**When** the plugin author reviews the sources register
**Then** the register shows for that sample its author, genre, source, basis for publication, date of writing with a reference to its evidence, the borders of its fragment, and a log of every change made to the text

### AC-03 (US-03) — happy path

**Given** the check set holds human samples from at least three authors and every human sample reaches 150 words
**When** the plugin author runs the check
**Then** the report states that all human samples reach 150 words, does not mark the human conclusion as inconclusive, and the register lists at least three authors, at least one of them another person

### AC-04 (US-04) — error

**Given** a new human sample receives an index above the human band of 25
**When** the plugin author runs the check
**Then** the report lists the sample as a false alarm and the run is reported as failed, the sample stays in the set and in the README table as a false alarm, and nobody removes it or excuses it

### AC-05 (US-05) — authorization: no text enters without a nameable basis for publication

**Given** a candidate is another person's modern text, a modern edition with editorial rights, or the plugin author's own text that still holds third-party personal data or confidential content after personal details are replaced
**When** the plugin author considers adding it to the check set
**Then** the candidate is not added, and the register records the refusal with the reason

### AC-06 (US-01) — domain invariant: a score is never a reason to change the set

**Given** the analyzer has been run on a text and gave an index the plugin author did not expect
**When** the plugin author considers replacing the text, dropping it or moving its fragment borders
**Then** the sample stays exactly as recorded, and the register accepts a refusal or a replacement only for provenance, basis for publication, a length below 150 words or above 600 words under the selection rule, or a defect of the file, never for the index

### AC-07 (US-02) — domain invariant: only texts written before 2023 count as human

**Given** a candidate whose date of writing is unknown or falls in 2023 or later
**When** the plugin author considers adding it as a human sample
**Then** the candidate is refused as human, and the register records the refusal with the reason

### AC-08 (US-02) — domain invariant: the text is not edited to suit the detector

**Given** a candidate is prepared as a sample
**When** the plugin author compares the sample with its source
**Then** the only differences are the fragment cut, removed invisible characters, and personal details replaced by neutral words of the same kind, and each such change is recorded in the register

### AC-09 (US-06) — cross-context

**Given** the two short human samples are replaced by longer texts
**When** the plugin author runs the check and refreshes the README table
**Then** neither the report nor the README table lists the old samples, and the changelog states that their earlier indexes are no longer part of the baseline

### AC-10 (US-07) — cross-context

**Given** the check set has the new human samples
**When** the plugin author refreshes the README table from the latest report
**Then** every row, the sample counts and the count of human samples reaching 150 words match the report, and the caption names each covered genre and each genre that is not covered with the reason

### AC-11 (US-08) — happy path

**Given** a text author opens the README after the refresh
**When** the text author reads the eval table and its note
**Then** the text author sees how many authors the human samples come from, which genres are covered, and a plain statement that the set holds classic, official and the plugin author's own texts and does not prove the detector safe for other kinds of modern text

### AC-12 (US-03) — error

**Given** a human sample of fewer than 150 words is in the set
**When** the plugin author runs the check
**Then** the report marks the human conclusion as inconclusive and the README note says so, and the step is not reported as done

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Length of each human sample | 150 to 600 words by the analyzer's own count; a candidate whose fragment under the selection rule exceeds 600 words is refused before any run | words column of the report; register refusal entry |
| Duration of a full run | ≤ 60 s for up to 30 samples | duration line of the report |
| Weight of the human sample files | ≤ 150 KB in total, counting human sample files only | summed size of the human sample files at review |
| Reproducibility | two runs on the same files give the same index and verdict for every sample | existing repeat-run check of the eval |
| Register completeness | 100% of human samples have every register field filled (author, genre, source, basis for publication, date of writing with evidence reference, fragment borders, change log), and every refused candidate has its reason | review checklist before shipping |

## 6.1 Security / privacy

- **Data classification:** public — every sample is committed to a public repository and stays readable by anyone.
- **Personal data touched:** none may remain; personal details in the plugin author's own texts (names, addresses, contacts, client data) are replaced by neutral words or the text is refused.
- **AuthZ/AuthN impact:** none; no new permission check and no new executable code, only text files and a register.
- **Abuse cases:**
  - Confidential or client content committed inside an own text: the candidate is refused, or the details are replaced and the change recorded.
  - A modern edition of a classic with editorial or translator rights: the candidate is refused; the original public-domain text is used instead.
  - A text with a false or unknown date passes as «before 2023»: the date and its evidence are a required register field, and a text without them is refused.
  - Choosing texts after seeing their scores: the register entry must exist before the sample, and a score is never a reason to change the set.
- **Security review:** N/A — no new authorization boundary and no personal data kept; the privacy read-through of each own text is part of AC-05.

## 7. Metrics / KPIs

- **Human samples reaching 150 words** — baseline: 0 of 2, target: all human samples at the first report after the step ships.
- **Authors behind the human samples** — baseline: 1 probable (the plugin author), target: at least 3 recorded in the register, at least one of them another person, at the first report after the step ships.
- **Genres covered or explained** — baseline: 0 of 4 covered with 150 words or more, target: each of the 4 genres either covered or named in the README as not covered with the reason, at the first refresh of the README table.
- **Human samples with a complete register entry** — baseline: 0 of 2 (no register exists), target: 100%, with every refused candidate carrying its reason, at the first report after the step ships.
- **Replacements or removals justified by an index** — baseline: 0, target: 0 in every later change to the human set.

## 8. Open questions

- [x] What evidence of the date of writing is enough for an own text (original file date, message date, publication date)? Default now: any dated original that the plugin author can point to, recorded as a reference in the register. — owner: Ihor Furman, due: before the first run. **Resolved 2026-10-03:** the default was adopted as rule 7 of `evals/samples/SOURCES.md`.
- [x] Which edition of a classic and which version of an official document is safe to use? Default now: the original public-domain text, never a modern edition with editorial rights, and the version of a law in force before 2023. — owner: Ihor Furman, due: before the first run. **Resolved 2026-10-03:** the default was adopted as rule 7 of `evals/samples/SOURCES.md`.
- [ ] Should the eval itself later check that every human sample has a register entry? Default now: no, the register is kept by the plugin author's discipline and reviewed before shipping. — owner: Ihor Furman, due: after this step ships
