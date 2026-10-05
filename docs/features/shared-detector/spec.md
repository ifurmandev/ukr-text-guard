---
status: Draft
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-05"
feature_size: "S"
---

# Spec — shared-detector

> **Glossary:** [CONTEXT](./CONTEXT.md) (feature) · [CONTEXT](../../../CONTEXT.md) (project)
> **Reference module / docs / channels used:** the three plugins' skill description files, read to list which shared file each plugin tells Claude to read; `evals/run.sh`, `README.md` and `.gitignore`, read to state facts about the current check; otherwise only the interview, `docs/idea-brief.md`, `docs/roadmap.md`, `docs/architecture-map.md` and the eval runner, read to verify facts.

## 1. Context

Three plugins of the marketplace carry the same files. One analyzer script is in all three, and four reference files are in two or three each, twelve plugin copies of five shared files. An installed plugin is a copy of its own folder, so it cannot read a file that sits outside it, and every plugin has to keep its own physical copy on the same path. Today a fix to the detector or to a rule list has to be made by hand in two or three places, and nothing tells the plugin author when one place was missed. The eval measures only one plugin copy per run, so it cannot notice that the other two differ.

There is no external trigger; the motive is internal. This is step 4 of the roadmap: the duplication grows with every change, and step 5 (a quiet hook) has to ship through a source of the shared files that is known to be identical in every plugin.

The committed approach is one shared source for the five shared files and a carry list that says which plugin carries which file (the guard plugin all five, the detector three, the editor four). A sync rewrites every diverged plugin copy from the shared source and lists what it rewrote, and a divergence check fails on a differing, missing or unlisted copy and names each file and plugin. The divergence check runs by itself in three ways: on demand, at the start of the eval's shell entry point where it stops the run before any sample is measured, and before every commit once the plugin author has done a one-time setup described in the README. The eval runner and its unit tests do not change. Rationale: the research found no tool that combines a per-file list of targets, a check that works without a server pipeline on Windows and a guarantee that the check really runs, so the three entry points cover each other, because the before-commit step does not travel to a fresh clone. The sharpest failure found is that the sync silently erases a change the plugin author made directly in a plugin copy in order to measure it with the eval, so the divergence report says plainly that copies are overwritten by the shared source and that such a change must be moved there first, and the README and the architecture map point to the shared source as the place to edit. The success criterion from the interview is that one fix touches one file and that any divergence fails the check with the file and the plugin named.

Checked on 2026-10-04: within each shared file, all plugin copies are byte-for-byte identical today (the analyzer in 3 plugins, the syntax-figures file in 3, and the other three files in 2 each), so the shared source can be seeded from any copy and the first sync rewrites nothing. The check looks at every folder under `plugins/`, today four, and recognises a shared file by its path inside the plugin.

Decision: the roadmap's open decision D2 (where the check runs) is closed here as «standalone, in the eval entry point and before every commit».

Sources: `docs/idea-brief.md` §6–§8, `docs/roadmap.md` step 4 and open decision D2, the CONTEXT glossaries. Decision overrides: the interview offered «a standalone script that the eval also calls»; the plugin author chose to add the before-commit step as well, and to leave the eval runner and its 74 unit tests untouched by calling the check from the shell entry point instead.

## 2. Goals

- The plugin author fixes a shared file in one place and brings every plugin up to date in one run.
- The plugin author learns about any divergence of plugin copies before it can be committed or measured, with the file and the plugin named.
- A text author who installs any of the plugins gets the same detector behaviour and the same files as before the step.

## 3. Non-goals

- Changing detector rules, weights, thresholds or the content of any shared file — a separate tuning job outside this iteration (`docs/idea-brief.md` §5); the first sync on the current files must rewrite nothing.
- Changing the eval runner or its unit tests — the eval keeps measuring one plugin copy per run, and a direct run of the runner does not perform the divergence check.
- Setting up an automated pipeline on a server — none exists and it would be a separate decision.
- Making installed plugins read the shared source at run time, or merging or renaming plugins — an installed plugin is a copy of its own folder and the plugin names are already installed by users.
- Proving that a shared file is correct, or that the copies installed on text authors' machines are current — the check proves only that the copies in the repository are equal.
- Sharing the skill description files — they differ in every plugin and stay separate.
- Forcing the before-commit step — it needs a one-time setup per clone and can be skipped, which is why the other two entry points exist.

## 4. User stories

### US-01: Fix a shared file once

**As a** plugin author
**I want** to edit each shared file in one place
**So that** a fix to the detector or a rule list is made once instead of in two or three plugins.

### US-02: Bring every plugin up to date

**As a** plugin author
**I want** one run that rewrites every diverged plugin copy from the shared source and lists what it rewrote
**So that** I see exactly what changed in which plugin.

### US-03: Be told when copies differ

**As a** plugin author
**I want** a check that fails when any plugin copy differs from the shared source and names each file and plugin
**So that** a missed copy cannot reach a release unseen.

### US-04: Be told on every path that matters

**As a** plugin author
**I want** the check to run on demand, at the start of the eval's shell entry point and before every commit
**So that** forgetting one path does not leave the copies unchecked.

### US-05: Know who carries what

**As a** plugin author
**I want** a carry list that says which plugin carries which shared file, and a check that reports a missing or an unlisted file
**So that** a plugin never lacks a file its skill description tells Claude to read and never holds a stale one.

### US-06: Not lose a change made in a copy

**As a** plugin author
**I want** the divergence report and the project documents to say that copies are overwritten by the shared source
**So that** a change I made directly in a plugin copy is moved to the shared source instead of being silently erased.

### US-07: Keep installed plugins working

**As a** text author
**I want** every plugin to keep the same files on the same paths and the detector to give the same results
**So that** my installed plugin works as before.

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** the plugin author has changed a shared file in the shared source
**When** the plugin author runs the sync
**Then** every plugin copy of that file named in the carry list equals the shared source, a copy that was missing is created together with the folders it needs inside that plugin, and the plugin author sees a list of each file and plugin that was rewritten or created

### AC-02 (US-02) — happy path

**Given** every plugin copy already equals the shared source
**When** the plugin author runs the sync
**Then** nothing is rewritten and the output says that all copies are up to date

### AC-03 (US-02) — error

**Given** the carry list names a file that the shared source does not hold, or names a plugin that does not exist (no folder of that name under `plugins/`), or has an entry that leads outside a plugin folder
**When** the plugin author runs the sync
**Then** the sync stops before writing anything and tells the plugin author which entry of the carry list is wrong

### AC-03b (US-02) — error

**Given** a plugin holds a shared file that the carry list does not give it
**When** the plugin author runs the sync
**Then** the sync still brings every other copy up to date, leaves that file in place, lists it as «left in place, delete by hand», and ends by saying that the divergence check will still fail until it is deleted; the sync never says that all copies are up to date while such a file exists

### AC-03c (US-03) — error

**Given** the carry list is wrong in one of the ways of AC-03, or the shared source holds a file that no plugin carries
**When** the plugin author runs the divergence check
**Then** the check fails, names the wrong carry list entry or the file that no plugin carries, and writes nothing

### AC-04 (US-03) — happy path

**Given** every plugin copy equals the shared source and matches the carry list
**When** the plugin author runs the divergence check
**Then** the check passes and states how many files in how many plugins it compared

### AC-05 (US-03) — error

**Given** a plugin copy differs from the shared source
**When** the plugin author runs the divergence check
**Then** the check fails, names each differing file and plugin, and says that copies are overwritten by the shared source, so a change made in a copy must be moved to the shared source before the sync

### AC-06 (US-05) — error

**Given** the carry list requires a file in a plugin that the plugin does not hold, or any folder under `plugins/` holds a file at the path of a shared file that the carry list does not give that plugin
**When** the plugin author runs the divergence check
**Then** the check fails and names the file, the plugin and whether the copy is missing or unlisted; an unlisted file is judged only by the path of a shared file, so any other file in a plugin, including files generated by running the analyzer, is not counted

### AC-07 (US-04) — error

**Given** the copies differ
**When** the plugin author starts the eval through its shell entry point
**Then** the divergence is reported, the run stops before any sample is measured, and the output states that the eval did not run and that the cause is a divergence, not a failed band; the run ends with a result code that differs from both success and a failed band, so a script can tell the three apart; the entry point always checks the whole repository that holds it, all plugins, whatever arguments it was given

### AC-08 (US-04) — error

**Given** the plugin author has done the one-time setup in this clone and the content about to be committed holds a diverged plugin copy
**When** the plugin author tries to commit
**Then** the commit is refused with the divergence report, and the check judges the content being committed, not the files left in the working folder; it judges both the shared source and the plugin copies as they are being committed, and it runs before every commit, whatever files the commit touches

### AC-08b (US-04) — error

**Given** the plugin author has done the one-time setup and the check cannot run, because no working interpreter is found or the check itself fails
**When** the plugin author tries to commit
**Then** the commit is refused with a message that says the check could not run, gives the reason, and says that a conscious bypass is `git commit --no-verify`

### AC-09 (US-04) — cross-context

**Given** the step is shipped
**When** the plugin author reads the README
**Then** the README names the one-time setup for the before-commit step, states that without it only the on-demand check and the eval entry point protect, and shows the command for the on-demand check and for the sync

### AC-10 (US-06) — authorization: a plugin copy is not a place to edit

**Given** the plugin author has changed a plugin copy directly and not the shared source
**When** the plugin author runs the divergence check or the sync
**Then** the check reports the copy as diverged, the sync overwrites it from the shared source and lists it, and the sync touches nothing outside the plugin copies named in the carry list

### AC-11 (US-06) — cross-context

**Given** the step is shipped
**When** the plugin author reads the README section on running the analyzer and the architecture map section on where to change detection logic or a rule list
**Then** both name the shared source as the place to edit and say that the sync must be run afterwards, and both name the eval's shell entry point as the only eval path that performs the divergence check, saying that a direct run of the eval runner does not

### AC-12 (US-03) — domain invariant: copies are equal byte for byte

**Given** a plugin copy differs from the shared source only in line endings or in an invisible mark
**When** the plugin author runs the divergence check
**Then** the check reports that copy as diverged, and the check changes no file in any case

### AC-13 (US-07) — cross-context

**Given** the sync has run and its result is committed
**When** the plugin author runs the eval on the analyzer of each of the three plugins in turn
**Then** every sample gets, on all three, the same index and the same row result as in the eval table committed in the README before this step

### AC-14 (US-07) — cross-context

**Given** the sync has run and its result is committed
**When** the plugin author compares the folder of each of the three plugins in the repository before and after the step
**Then** every file that the plugin's skill description tells Claude to read is present on the same path as before the step, and no file was added, removed or moved

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Duration of the divergence check | ≤ 2 s for 5 shared files in 3 plugins | timed standalone run on the plugin author's machine |
| Duration of the sync | ≤ 2 s for 5 shared files in 3 plugins | timed standalone run |
| Idempotence | the second sync in a row rewrites 0 files; the first sync on the current files rewrites 0 files | output of the two runs |
| Unchanged eval | 0 changed lines in the eval runner and in its unit tests; 74 of 74 existing unit tests pass | diff of the step and the test run |
| Completeness of detection | each of the 4 kinds (differing, missing, unlisted, differing only in line endings) is caught by at least 1 automated test | test run of the new unit tests |
| Environment | works with each of the 3 interpreters the eval entry point already probes, as far as they are present on the machine, with 0 imports outside the standard library | run on the plugin author's Windows shell with each present interpreter |

## 6.1 Security / privacy

- **Data classification:** public — every file involved is committed to a public repository.
- **Personal data touched:** none.
- **AuthZ/AuthN impact:** none; no permission check is added, and the sync writes only to the plugin copies named in the carry list, refusing an entry that points outside a plugin folder.
- **Abuse cases:**
  - A plugin copy is changed so that one plugin carries different detector code than the others: the divergence check reports it and names the plugin.
  - A carry list entry points outside the plugin folders: the sync refuses it before writing anything.
  - The before-commit step is skipped on purpose or never set up: the on-demand check and the eval entry point still report the divergence, and the README states this limit.
- **Security review:** N/A — no new authorization boundary and no personal data; the only write path is limited by the carry list (AC-10).

## 7. Metrics / KPIs

- **Hand-edited plugin copies per fix** — baseline: 2 to 3 places for one shared file, target: 1 place (the shared source), at the first fix after the step ships.
- **Plugin copies that the divergence check confirms equal to the shared source** — baseline: 0 of 12 (no check exists), target: 12 of 12, at the step's first report.
- **Divergence kinds caught by the check** — baseline: 0 of 4 (no check exists), target: 4 of 4, at the step's first run of the unit tests.
- **Samples with an unchanged index on all three analyzer copies** — baseline: 11 of 11 on the guard copy only, target: 11 of 11 on each of the three copies, at the step's first report.

## 8. Open questions

- [x] Should the sync also delete a file a plugin holds that the carry list does not give it? **Resolved 2026-10-05: no.** The sync deletes nothing and only warns (AC-03b); the check reports the file and the plugin author deletes it, because a deletion cannot be undone by the sync. — owner: Ihor Furman
- [ ] Should plugin versions change when a shared file changes, so that installed copies refresh? Default now: no, the versions stay as they are in this step. — owner: Ihor Furman, due: before the first release after this step
- [x] Should a direct run of the eval runner, which skips the shell entry point, later also perform the divergence check? **Resolved 2026-10-05: no.** The check is not added to `run_eval.py`; it stays at three entry points (on demand, `evals/run.sh`, before every commit), and the README and the architecture map name the shell entry point as the only checked eval path (AC-11). — owner: Ihor Furman
- [x] Should the repository pin line endings so that an editor setting cannot cause a divergence? **Resolved 2026-10-05: yes.** A committed `.gitattributes` sets `eol=lf` for `shared/` and for the paths of the plugin copies (`plugins/*/skills/*/scripts/analyze.py` and `plugins/*/skills/*/references/` for the four reference files). The check still reports a difference in line endings as divergence (AC-12): the pin makes it rare, it does not remove the kind. The pin changes no file content, because the shared files already use LF, so the first sync still rewrites nothing. — owner: Ihor Furman
- [ ] Should a plugin folder that exists but holds no files count as an existing plugin for the working-tree reader? Found by review 2026-10-05 (tools/shared_sync.py:65-70): plugin names come only from file paths, so an empty `plugins/<p>/` is reported as missing and the sync refuses instead of creating the copy (AC-01, AC-03). Deferred: the Git index has no empty folders, so the staged check is unaffected. — owner: Ihor Furman, due: 2026-10-19
- [ ] Should a source file saved with CRLF be reported as a line-ending problem of the source instead of as a difference of every copy? Found by review 2026-10-05 (tools/shared_sync.py:114): only «copy has CRLF, source has LF» gets `shared.line_endings` (AC-12). Deferred: the case is still reported as divergence and `.gitattributes` pins `eol=lf` for `shared/`. — owner: Ihor Furman, due: 2026-10-19
