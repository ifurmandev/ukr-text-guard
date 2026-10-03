# Changelog — ukr-text-eval

## ukr-text-eval — a pass/fail check of the detector against expected score bands

**What:** The plugin author can run one command and see whether the detector still scores human samples low and AI samples high. The report lists every sample with its category, index, word count and reliability, then separates false alarms (human text flagged), misses (AI text not flagged), errors and known gaps. The exit code alone says pass (0) or fail (1).

**Why:** Until now nobody could tell from a measurement how often the detector wrongly flags human text. The bands (human at most 25, ordinary AI at least 26) are fixed before the run, so the check tests the detector instead of mirroring it. See [spec](spec.md) §1–§2. Two decisions carry the design: bypass samples stay visible as *known-gap* in a plain list file ([ADR-0001](adr/0001-keep-known-gaps-in-a-plain-list-file.md)), and the outcome is signalled by exit code only ([ADR-0002](adr/0002-signal-the-outcome-by-exit-code-only.md)).

**How to use:**

```
python evals/run_eval.py [--plugin ukr-text-guard|ukr-text-detector|ukr-text-editor]
bash   evals/run.sh      [--plugin NAME]
```

Samples go in `evals/samples/` as `human-*.txt` or `ai-*.txt`. An AI sample the detector is known to miss is excused only by a line in `evals/known-gaps.txt`. Full contract: [cli.md](contracts/cli.md).

First real run on `ukr-text-guard`: 10 samples, passed. 5 of 7 ordinary AI samples reach index 51 or more. Both human samples are under 150 words, so the report marks the human conclusion as **inconclusive**. Sample set breadth is roadmap step 3.

**Operational notes:**
- Migration: <!-- none -->
- Feature flag / config: <!-- none --> (no detector rules, weights or thresholds changed)
- Rollback: revert the merge. The change adds `evals/` only and touches no plugin file.

**Acceptance criteria delivered:** AC-01 … AC-19: the report and exit code for pass, false alarm, drift, miss, known-gap (and its misuse), short-evidence marking, analyzer failure, sample independence, per-plugin copy choice, unclassified/ignored items, empty categories and a missing detector copy.
