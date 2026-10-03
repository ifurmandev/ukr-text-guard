# API sync report — ukr-text-eval

Interface kind: **cli** (read from `sad.md` `target_surfaces`, not re-derived). Contract: [cli.md](cli.md). No `events.md`: no async flows.

`data-model.md` is absent. **Legal fast-lane skip**: no schema change (sad §5 declares no entity, no staged migrations, no datastore, spec introduces no entity). Inputs are text files, so there is no existing schema to derive from either.

## A. Field origins

| path | origin | confidence |
|---|---|---|
| option `--plugin` | spec AC-11, AC-18, sad §8 Configuration | high |
| option `--root` | sad §4 seed 4, §8 Configuration | high |
| input samples folder, prefix rule | spec AC-12, AC-17, architecture-map naming convention | high |
| input known-gap list format | ADR-0001, sad §5 | high |
| input detector path and invocation | sad §2 (analyze.py:513 contract), §8 Encoding | high |
| output per-sample fields (index, word count, reliability) | analyzer JSON keys via sad §2, spec AC-08 | high |
| output summary counts | spec AC-02, AC-08, AC-12, AC-17 | high |
| output duration | spec §6 Run time | high |
| exit codes 0 and 1 | spec AC-16, AC-19, ADR-0002 | high |
| failure kind names | proposal, no repo error registry | medium |
| exact report wording and layout | not fixed by spec or SAD, only the facts and their order | medium |

## B. Drift checklist

1. **Endpoint ↔ data-model** (core) — ✓ adapted: every command maps to a §4 user story (`run_eval.py` to US-01 through US-08, `run.sh` to the documented command), no entity involved.
2. **Error code ↔ repo error definition** (core) — ✓ with note: no error registry exists in the repo, so the `eval.*` names are the contract's proposal, to be reconciled if the repo defines a registry.
3. **Validation ↔ constraint** (core) — ✓ adapted: bands 25, 15, 26, 51, 150 words and 10 s match sad §8 Configuration and spec §1, §5, §6. Spec §8 OQ-1 is resolved at 150.
4. **Contract ↔ sequence** (supporting) — ✓: every `alt` branch of the five §6 flows has a report section or a failure kind (no detector copy, unclassified, ignored, bad entry, missing category, six analyzer failure reasons, false alarm, drift, miss, gap may be closed, inconclusive, exit 1 and 0, runner error).

### Back-feed coverage (AC to contract)

| AC | Where |
|---|---|
| AC-01 | cli.md §4 per-sample lines, verdict line, exit 0 |
| AC-02 | §4 summary, high-level count |
| AC-03 | §4 false alarms, `eval.false_alarm` |
| AC-04 | §4 notes, drift |
| AC-05 | §4 misses, `eval.miss` |
| AC-06 | §4 notes, gap may be closed |
| AC-07 | §4 known-gap list |
| AC-08 | §4 per-sample fields, summary, inconclusive |
| AC-09 | `eval.analyzer_failure` |
| AC-10 | §3 fresh process per sample, no order flag |
| AC-11 | §2 `--plugin`, §4 header |
| AC-12 | §3 prefix rule, `eval.unclassified_sample`, summary counts |
| AC-13, AC-14 | `eval.bad_known_gap` |
| AC-15 | `eval.missing_category` |
| AC-16 | §5 exit codes |
| AC-17 | §3 ignored items, summary |
| AC-18 | `eval.missing_detector_copy` |
| AC-19 | §4 notes, §5 |

All 19 ACs map to a contract element. Every command and option maps to a user story.

## Findings to resolve (2 flags, none core)

Fewer than 3 flags and no core failure, so the run was not paused. Both are holes upstream, saved as open questions with the producing stage as owner:

- **OQ-A, sequence and AC gap: invalid command line.** A bad or unknown option has no §6 branch and no AC. A standard argument parser exits with code 2, which would break «only 0 or 1» (ADR-0002). The contract says: usage error prints usage and exits 1. Owner: `sequences` or `specify` (add a branch or an AC), due before the contract is finalized.
- **OQ-B, spec gap: known-gap list file missing.** No AC says what happens when `evals/known-gaps.txt` does not exist. Proposed: treated as an empty list, no failure. Owner: `specify` or `clarify`, due before the contract is finalized.

Also noted, not a drift: the current `evals/run.sh` takes no arguments and calls `python3`. The contract's `run.sh` form (argument pass-through, interpreter probe) is the target from sad §5 and is built in implementation.
