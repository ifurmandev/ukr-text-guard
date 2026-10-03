---
status: Accepted
owner: "Ihor Furman"
reviewers: ["Tech Lead"]
updated_at: "2026-10-03"
feature_size: "XS"
ticket: "roadmap step 2 — readme-eval-table"
---

# 0001 — Maintain the eval table by hand from one report

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Ihor Furman (plugin author) with the architect, during the design walk

## Context

The README eval table is a published copy of what one eval run reports. Someone has to produce it, and its cells must equal the report (spec §6 Accuracy). The spec fixes the contents and the six-value result mapping (AC-08), and it lists generating the table and checking drift as non-goals with no roadmap step behind them (spec §3, §8). This ADR records the choice of how the table is produced and kept true now.

## Decision drivers

- Spec §3: changing the eval runner is outside an XS change.
- Spec §6 Footprint: 2 files changed outside docs, 0 code files.
- Spec §6 Accuracy: 100% of cells equal the report; the check is a reviewer comparing the table with a pasted report.
- Roadmap: step 2 runs in parallel with steps 3 and 4 and must not bind them to refresh the table.

## Considered options

1. **By hand from one report** — the plugin author copies the rows from the report, applies the result mapping, and pastes the report into the pull request for the reviewer.
2. **The runner prints the table** — deferred, not rejected on merit: a new report mode would emit the markdown rows, but spec §3 excludes changing the runner from this step.
3. **A drift check on top of the table** — deferred, not rejected on merit: a script would compare the README rows with a fresh run, but spec §3 and §8 leave it without a roadmap step.

## Decision outcome

**Chosen:** Option 1. It is the only option that keeps the runner untouched and the footprint at 2 files, and the reviewer comparison already covers accuracy for one change. Options 2 and 3 are listed as deferred because they change code, which spec §3 rules out for this step; they belong to a later roadmap step if the plugin author adds one (spec §8, first open question).

## Consequences

**Positive**
- No code changes; the eval, its tests and the three detector copies stay as they are.
- The change is one reviewable diff with the report pasted next to it.

**Negative**
- A hand-typed cell can differ from the report; only the review catches it.
- The table goes stale silently when samples, bands or a detector copy change; the caption's plugin and date are the only signal.

**Neutral**
- Moving to option 2 later is mechanical: the row format and the result mapping are already fixed by AC-08, so a printer would produce the same rows.

## Links

- Spec: [[../spec.md]] (§3, §6, §8, AC-08, AC-10)
- SAD: [[../sad.md]] §4, §11
