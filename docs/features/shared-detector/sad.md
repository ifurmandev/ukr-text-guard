---
status: Draft
owner: "Ihor Furman"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-10-05"
feature_size: "S"
target_surfaces: [cli]
---

# Software Architecture Document — shared-detector

<!-- 12 Arc42 sections. Empty section → <!-- N/A: <one-line reason> -->. -->
<!-- C4 Context (L1) lives inline in §3. C4 Container (L2) lives inline in §5. -->
<!-- Numbers in §10 come VERBATIM from spec.md §6 NFR — no inventing, no rounding. -->

## 1. Introduction and goals

**Intent.** The plugin author edits each shared file in one place (a shared source) and brings every plugin copy up to date in one run, with the run listing what it rewrote. Any divergence between a plugin copy and the shared source is reported, with the file and the plugin named, before the copies can be committed or measured by the eval. A text author who installs any of the three text plugins gets the same files on the same paths and the same detector results as before the step.

**Top-3 quality goals (1-liners; full scenarios in §10):**

1. **Completeness of detection** — every one of the 4 divergence kinds (differing, missing, unlisted, differing only in line endings) is caught and reported with the file and the plugin named.
2. **Safety of writes** — the sync is idempotent, writes byte for byte, writes only to plugin copies named in the carry list, and never deletes a file.
3. **Unchanged behaviour and portability** — the eval runner, its unit tests and every installed plugin behave as before; each command takes ≤ 2 s; only the standard library, on each interpreter the eval entry point already probes.

**Stakeholders.**

| Role | Interest | Sign-off owner? |
|---|---|---|
| Plugin author | Edits the shared source, runs the sync and the divergence check, commits | No |
| Text author | Installs a plugin and expects it to work as before; does not run the tooling | No |
| Tech Lead | SAD approval | Yes |

## 2. Constraints

**Technical.**
- Python 3, standard library only, with no import outside it. The code is written to run on Python 3.8 or newer: the repository pins no minimum, the local interpreter is 3.12.10, and no module newer than 3.8 is used (no `tomllib`, no `match`). The interpreters are the three that `evals/run.sh` already probes, in this order: `python3`, `python`, `py`.
- Bash for `evals/run.sh` and the before-commit step (Git Bash on Windows); Git 2.9 or newer, because the before-commit step is activated through `core.hooksPath`.
- Layout convention of the repository: a plugin is `plugins/<name>/skills/<name>/`; the skill folder carries the shared files at fixed paths inside it (`scripts/`, `references/`).
- No datastore: the only state is files in the repository.

**Organisational.**
- Size S: about 2 to 5 PRs, about one week.
- No deadline is set in the spec.
- One maintainer, who is also the reviewer: Ihor Furman, the plugin author.

**Conventions.**
- Commit prefixes `feat:`, `chore:`, `test:`, `docs:`; code, tests, test names and commit messages in English; the README and product texts in Ukrainian.
- Tests are `unittest` tests run with `python -m unittest discover <dir>`; the 74 existing tests in `evals/tests/` and the eval runner `evals/run_eval.py` are not changed.
- Machine lines of the output follow the eval runner: `error <code>: <message>` and a final `result: <passed|failed>` line, in English.

**Regulatory / external.**
- None. Every file involved is committed to a public repository and holds no personal data (spec §6.1).

## 3. Context and scope

The marketplace ships three text plugins that each carry their own physical copy of the same shared files, because an installed plugin is a copy of its own folder. This feature adds the tooling that keeps those copies equal to one shared source: a sync that rewrites them, and a divergence check that fails when they differ. It sits between the plugin author and the plugin folders; the text author only sees its result, as unchanged plugins.

<!-- brownfield: architecture-map.md (reflects_commit e6a83b1, plugins unchanged since): 4 plugins under plugins/, one skill each, no shared source, no CI, evals/run.sh as the only entry point of the eval -->

**External systems (in / out):**

| Actor or system | Type | Interaction |
|---|---|---|
| Plugin author | Person | Edits the shared source, runs the sync and the divergence check, runs the eval, commits |
| Text author | Person | Installs a plugin through Claude Code; never touches the tooling |
| Git | System (external) | Runs the before-commit step; holds the content being committed |
| Claude Code | System (external) | Installs and loads the plugin folders from the marketplace |
| Eval entry point | System (internal, existing) | Runs the divergence check first, then the eval runner, which is unchanged |
| Plugin folders | System (internal, existing) | Hold the plugin copies; the only place the sync writes |

**C4 Context (L1):**

```mermaid
C4Context
    title shared-detector — System Context

    Person(author, "Plugin author", "Maintains the plugins, edits the shared source, runs the eval")
    Person(writer, "Text author", "Installs a plugin and checks Ukrainian texts")

    System(tooling, "Shared-file tooling", "Shared source, carry list, sync and divergence check")
    System(plugins, "Plugin folders", "Three text plugins, each with its own copy of the shared files")
    System(evals, "Eval entry point", "Runs the divergence check, then measures samples; existing")
    System_Ext(git, "Git", "Holds the content being committed and runs the before-commit step")
    System_Ext(claude, "Claude Code", "Installs and loads the plugin folders")

    Rel(author, tooling, "Edits the shared source, runs sync and check")
    Rel(author, evals, "Runs the eval")
    Rel(author, git, "Commits")
    Rel(git, tooling, "Runs the check before every commit")
    Rel(evals, tooling, "Runs the check first")
    Rel(tooling, plugins, "Compares copies, rewrites diverged ones")
    Rel(claude, plugins, "Installs and loads")
    Rel(writer, claude, "Uses the plugins")
```

## 4. Solution strategy

**Target surface.** `cli` (`target_surfaces: [cli]` in the frontmatter): a console application with two commands, `check` and `sync`, flags and exit codes. The before-commit hook and `evals/run.sh` are thin callers of that one command, not surfaces. One surface, so there is no multi-surface ADR and no UI-architecture decision.

**Top strategic choices (the seeds for ADRs):**

1. **One plan, two commands.** The core builds a plan from three inputs: the shared source, the carry list and a tree of plugin copies. `check` renders the plan and never writes. `sync` validates the carry list first, then applies the plan, then renders it. Both use the same comparator, so the sync can never write something the check would still call a divergence, or call «up to date» something the check would fail. Serves quality goals 1 and 2.
2. **Exact bytes.** Content is compared and written as bytes, with no normalisation of line endings or invisible marks (spec AC-12), and the sync never deletes a file, so an unlisted file is reported and left for the author (spec §8, first question). Serves quality goal 2.
3. **Three entry points, one exit-code contract.** The on-demand command, `evals/run.sh` and the before-commit hook all call the same command and read the same codes: 0 equal, 3 divergence or wrong carry list, 4 the check could not run. A check that could not run is never read as a pass. The eval entry point stops before any sample on any non-zero code and ends with 3 or 4, never with the exit code 0 or 1 that the runner uses. Serves quality goals 1 and 3.
4. **The before-commit step judges the staged content, not the working folder.** The core reads content through a tree reader with two implementations, the working folder and the Git index → [ADR-0001](adr/0001-read-staged-content-from-the-git-index.md). Serves quality goals 1 and 2.
5. **The hook ships in the repository and is switched on once per clone.** A committed `.githooks/pre-commit` activated by `git config core.hooksPath .githooks` → [ADR-0002](adr/0002-ship-the-hook-in-githooks-with-core-hookspath.md). Serves quality goal 1 without adding a dependency (goal 3).
6. **The shared source mirrors the in-skill paths, and the carry list is data.** `shared/` holds the five files at the path they have inside a skill folder, and `shared/carry.json` maps each path to the plugins that carry it → [ADR-0003](adr/0003-mirror-in-skill-paths-under-shared-with-a-json-carry-list.md). Serves quality goals 1 and 3 (no file added to any plugin).

Each tactical decision in later sections should trace to one of these seeds. Tactical decisions that *contradict* a strategic choice are red flags — surface them in §11.

## 5. Building block view

There is no layering to speak of: the product is one Python command made of pure functions (read a tree, load the carry list, build a plan, render it, apply it) behind a thin argument parser, plus two short Bash callers. This matches the repository, where the only code beside the detector is the eval runner, a single script with pure judging functions and a thin `main`. The plan is a plain value, so the check, the sync and the tests all consume the same thing.

**Internal decomposition:**

```
shared/                         the shared source (new)
├── carry.json                  which plugin carries which shared file
├── scripts/analyze.py
└── references/                 ai-markers.md, lexicon.md, style-toolkit.md, syntax-figures.md
tools/                          (new)
├── shared_sync.py              check and sync: tree readers, carry list, plan, report, apply, exit codes
└── tests/test_shared_sync.py   unit tests for the 4 divergence kinds and the guards, plus one test on a real temporary Git repository
.githooks/pre-commit            Bash: runs `check --staged` before every commit (new)
evals/run.sh                    Bash: runs `check` first, then the eval runner (extended)
evals/run_eval.py, evals/tests/ unchanged
plugins/<p>/skills/<p>/...      the plugin copies, on the same paths as before
```

**C4 Container (L2):**

```mermaid
C4Container
    title shared-detector — Containers

    Person(author, "Plugin author", "Edits the shared source, runs sync and check, commits")
    System_Ext(git, "Git", "Holds the index and runs the before-commit hook")

    Container_Boundary(repo, "Repository tooling") {
        Container(cli, "shared_sync.py", "Python 3, standard library", "check and sync commands; reads trees, builds the plan, reports, rewrites diverged copies")
        Container(hook, ".githooks/pre-commit", "Bash", "Runs check on the staged content before every commit")
        Container(runsh, "evals/run.sh", "Bash", "Runs check first, then the eval runner; existing, extended")
        Container(runner, "run_eval.py", "Python 3", "Measures samples against expected bands; unchanged")
        ContainerDb(source, "Shared source and carry list", "Files under shared/", "Five shared files and carry.json")
        ContainerDb(copies, "Plugin copies", "Files under plugins/", "Each plugin's copy of the shared files it carries")
    }

    Rel(author, cli, "Runs check and sync")
    Rel(author, runsh, "Runs the eval")
    Rel(author, git, "Commits")
    Rel(git, hook, "Runs before every commit")
    Rel(hook, cli, "check --staged")
    Rel(runsh, cli, "check, before any sample")
    Rel(runsh, runner, "Runs when check passes")
    Rel(cli, source, "Reads")
    Rel(cli, copies, "Reads, rewrites diverged copies")
    Rel(cli, git, "Reads the index", "git plumbing")
    Rel(runner, copies, "Reads the guard copy of analyze.py")
```

## 6. Runtime view

Three flows are seeded here, one per entry point; the `sequences` stage then maps every acceptance criterion of the spec to a flow, a branch or an explicit N/A. Participants are the containers of §5.

**Critical flow 1: sync** (spec AC-01, AC-02, AC-03, AC-03b, AC-10)

```mermaid
sequenceDiagram
    actor Author
    participant CLI as shared_sync.py
    participant Source as Shared source and carry list
    participant Copies as Plugin copies
    Author->>CLI: sync
    CLI->>Source: read the carry list and the shared files
    alt a carry list entry is wrong
        CLI-->>Author: names the wrong entry, nothing is written, result failed
    else the carry list is valid
        CLI->>Copies: compare every carried copy byte for byte
        CLI->>Copies: rewrite or create each diverged or missing copy
        Copies-->>CLI: written
        CLI-->>Author: lists each file and plugin rewritten or created, or says all copies are up to date
        opt a plugin holds a shared file the carry list does not give it
            CLI-->>Author: lists it as left in place, delete by hand, and says the check still fails
        end
    end
```

**Critical flow 2: check before every commit** (spec AC-08, AC-08b)

```mermaid
sequenceDiagram
    actor Author
    participant Git
    participant Hook as pre-commit hook
    participant CLI as shared_sync.py
    Author->>Git: commit
    Git->>Hook: run before the commit
    Hook->>CLI: check the staged content
    CLI->>Git: read the index
    Git-->>CLI: staged shared source, carry list and plugin copies
    alt every copy equals the shared source
        CLI-->>Hook: passed
        Hook-->>Git: allow the commit
    else a divergence exists
        CLI-->>Hook: report naming each file and plugin
        Hook-->>Git: refuse the commit
        Git-->>Author: commit refused with the report
    else the check could not run
        Hook-->>Git: refuse the commit with the reason and the no-verify bypass
        Git-->>Author: commit refused, the check could not run
    end
```

**Critical flow 3: check at the start of the eval** (spec AC-07)

```mermaid
sequenceDiagram
    actor Author
    participant RunSh as evals/run.sh
    participant CLI as shared_sync.py
    participant Runner as run_eval.py
    Author->>RunSh: run the eval
    RunSh->>CLI: check the whole repository
    alt every copy equals the shared source
        CLI-->>RunSh: passed
        RunSh->>Runner: run all samples
        Runner-->>Author: report and exit code 0 or 1
    else a divergence exists
        CLI-->>RunSh: report naming each file and plugin
        RunSh-->>Author: the eval did not run, the cause is a divergence, exit code 3
    else the check could not run
        RunSh-->>Author: the eval did not run, the check could not run, exit code 4
    end
```

## 7. Deployment view

<!-- N/A: nothing is deployed, the tooling runs on the plugin author's machine -->

The tooling has no deployment unit of its own. It runs on the plugin author's machine on demand, at the start of the eval and before a commit, and it ships inside the repository like the eval runner. Monitoring is the output and the exit code of each run; no threshold applies, because one run reads about 20 files.

## 8. Crosscutting concepts

| Concept | Convention | Where defined |
|---|---|---|
| Logging | None: no log file. A run prints its report to stdout and errors to stderr. | here |
| Report format | English lines `error shared.<code>: <file> <plugin> <detail>` for each finding, ending with `result: passed` or `result: failed`. Codes: `shared.differing`, `shared.line_endings`, `shared.missing`, `shared.unlisted`, `shared.orphan_source`, `shared.carry_entry`, `shared.cannot_run`. The notice that copies are overwritten by the shared source is printed whenever a copy differs. | `evals/run_eval.py` (`eval.*` codes) |
| Exit codes | `check`: 0 every copy equals the shared source and matches the carry list; 3 any divergence or a wrong carry list; 4 the check could not run. `sync`: 0 every copy equals the shared source after the run; 3 stopped by a wrong carry list, or an unlisted file remains; 4 could not run. Any unexpected exception is caught in `main` and exits 4, because the Python default 1 would be read by the eval as a failed band. | here |
| Error handling | Guard clauses return a finding, not an exception; the plan is a plain value that the report renders. | `evals/run_eval.py` |
| Authentication / authorization | N/A. The only write boundary: the sync writes only to `plugins/<p>/skills/<p>/<shared path>` for entries of the carry list that passed validation; an absolute path, a path with `..` or one that leaves the plugin folder is rejected before anything is written. | spec §6.1 |
| Paths and bytes | Paths in `carry.json` are relative with forward slashes. Files are read and written as bytes with no line-ending translation. A missing folder is created only inside the carrying plugin. | here |
| Write order | The whole carry list is validated first, then written. Each copy is written directly. An interrupted run can leave a short copy; the next check reports it and the next sync repairs it, because both are idempotent. | here |
| Interpreter lookup | `python3`, `python`, `py` in this order; the first that runs `-c "import sys"`. Identical in `evals/run.sh` and in the hook. | `evals/run.sh` |
| ID strategy / events / internationalisation | N/A. The report is English like the eval report; the README is Ukrainian. | — |

## 9. Architecture decisions

| # | Title | Status | Section |
|---|---|---|---|
| 0001 | Read the staged content from the Git index in the before-commit check | Accepted | §4 |
| 0002 | Ship the before-commit hook in a committed `.githooks` folder activated through `core.hooksPath` | Accepted | §4 |
| 0003 | Mirror the in-skill paths under `shared/` and list the carriers in `shared/carry.json` | Accepted | §4 |

ADR files live under `docs/features/shared-detector/adr/NNNN-<title>.md`.

## 10. Quality requirements

Each top-3 goal from §1 expanded into a full scenario. Numbers are copied from spec §6.

**QG-1. Completeness of detection**
- **When:** a plugin copy differs from the shared source, is missing although the carry list requires it, is a file at a shared path that the carry list does not give that plugin, or differs only in line endings.
- **Then:** the check fails and names the file and the plugin; each of the 4 kinds is caught by at least 1 automated test.
- **How verify:** one unit test per kind on an in-memory tree; one integration test on a real temporary Git repository for the index reader (ADR-0001), including a copy that is fixed in the working folder but staged with a divergence; tests of exit codes 3 and 4 for `evals/run.sh`.

**QG-2. Safety of writes**
- **When:** the sync runs on the current files, and again right after a sync.
- **Then:** the first sync on the current files rewrites 0 files; the second sync in a row rewrites 0 files; the sync writes only into copies named in the carry list.
- **How verify:** a unit test that counts writes on an in-memory tree; a carry list entry such as `../x` makes the sync write nothing; the output of two runs in the repository.

**QG-3. Unchanged behaviour and portability**
- **When:** the step is complete and the tests and timings are run.
- **Then:** 0 changed lines in the eval runner and in its unit tests; 74 of 74 existing unit tests pass; the check takes ≤ 2 s and the sync takes ≤ 2 s for 5 shared files in 3 plugins; it works with each of the 3 interpreters the eval entry point probes, as far as they are present, with 0 imports outside the standard library.
- **How verify:** `git diff --stat` shows no change under `evals/run_eval.py` and `evals/tests/`; `python -m unittest discover evals/tests`; a timed standalone run on the plugin author's Windows shell with each present interpreter.

## 11. Risks and technical debt

<!-- 🎯 Why: ⭐ collects EVERYTHING that can break — not only the technical. Without §11 risks get
     discussed at standups and lost; debt lives only in the head of whoever accepted it.
     📋 Write: a risk/debt table — severity — mitigation — owner. Accepted debt in its own block.
     📌 The first risk is often a product risk, not a technical one. That's normal. -->

<!-- Severity literals: Low / Medium / High for regular risks; "Open question" for rows created by
     a Save-as-OQ resolution during the Socratic walk (see references/socratic.md). -->

| Risk / debt | Severity | Mitigation | Owner |
|---|---|---|---|
| <e.g. Worker lag may reach hours during a downstream outage> | Medium | <alert >10 min, on-call playbook, retry backoff> | <DevOps> |
| <e.g. No event-schema versioning in v1> | Medium | <ADR-NNNN planned for v2, tolerate unknown fields> | <Backend> |
| Open architectural decision: <decision-headline> | Open question | Resolve before <stage trigger or YYYY-MM-DD>; <inline rationale from the Save-as-OQ> | <owner> |

**Accepted debt (acceptable in v1, plan to fix later):**
- <e.g. the entity is immutable / unversioned — OK for v1, may need audit versioning in v2>

## 12. Glossary

<!-- 🎯 Why: ⭐ the DOMAIN GLOSSARY that ends arguments a year later («checkpoint — weekly or
     biweekly? quarter — calendar or fiscal?»).
     📋 Write: a term / meaning table. Business + technical terms mixed.
     📌 e.g. «Lesson | a unit inside a course made of blocks (text, video)». -->

| Term | Meaning |
|---|---|
| <e.g. domain object A> | <its meaning in this domain> |
| <e.g. domain object B> | <its meaning> |
| <e.g. domain invariant name> | <the rule, in plain language> |
