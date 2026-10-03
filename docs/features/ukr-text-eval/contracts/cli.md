---
status: Draft
owner: "Ihor Furman"
updated_at: "2026-10-03"
feature_size: "S"
surface: cli
derived_from: ["spec.md §4-§5", "sad.md §4, §6, §8", "adr/0001", "adr/0002"]
---

# CLI contract — ukr-text-eval

Derived, not hand-written: every row below traces to a spec acceptance criterion, a `sad.md` flow or an ADR (see `api-sync-report.md`). There is no `data-model.md` and no schema change, so no field comes from a schema. Inputs are text files and the output is a report plus an exit code.

## 1. Commands

```
python evals/run_eval.py [--plugin NAME] [--root DIR]
bash   evals/run.sh      [--plugin NAME] [--root DIR]
```

| Command | Meaning | Source |
|---|---|---|
| `run_eval.py` | The check. Discovers samples, analyses each, judges, prints the report, sets the exit code. All verdict logic lives here | sad §5, US-01 |
| `run.sh` | Thin delegate. Probes `python3`, `python` and `py`, checks that the candidate really starts, passes every argument through unchanged. Adds no flags and no verdicts | sad §5, §11 |

## 2. Options

| Option | Default | Meaning | Source |
|---|---|---|---|
| `--plugin NAME` | `ukr-text-guard` | Which plugin's detector copy to measure. Allowed names: `ukr-text-guard`, `ukr-text-detector`, `ukr-text-editor`. One copy per run | AC-11, AC-18, sad §8 |
| `--root DIR` | repo root derived from the script's own location | Where `plugins/` and `evals/` are looked up. A test seam, not part of the author's daily use | sad §4 seed 4, §8 |
| `-h`, `--help` | | Prints usage, exits 0 | convention |

No other options. There is deliberately no order flag (sad §8 Determinism), no `--json` (ADR-0002), no band or limit flags (bands are named constants, spec §6 «0 edits to expected bands»).

An invalid command line (unknown option, missing value) prints usage and exits 1, not 2, so that only 0 and 1 exist (ADR-0002). See OQ-A in `api-sync-report.md`.

## 3. Inputs

| Input | Location under the root | Rule | Source |
|---|---|---|---|
| Samples | `evals/samples/` | Plain `*.txt` files directly in the folder. `human-` prefix is human, `ai-` prefix is AI, any other plain text file, and any file whose extension is `.txt` in another letter case (such as `.TXT`), is unclassified. Non-text files and subfolder contents are ignored | AC-12, AC-17 |
| Known-gap list | `evals/known-gaps.txt` | One AI sample name (file name without `.txt`) per line, optional `# reason`. A name that does not exist, or names a human sample, is an error. A missing file is treated as an empty list (OQ-B) | AC-13, AC-14, ADR-0001 |
| Detector copy | `plugins/<NAME>/skills/<NAME>/scripts/analyze.py` | Started as `sys.executable analyze.py FILE --json` in a fresh process with `PYTHONUTF8=1` and a 10 s limit | AC-09, AC-10, sad §2 |

## 4. Output

Plain text on stdout, UTF-8, English prose, sample names untouched. Nothing is written to files and no log exists. The contract fixes **which facts appear**, not the exact wording. Sections in this order:

1. **Header** — the plugin whose copy was used (AC-11).
2. **Per-sample lines**, in sorted name order — name, category (human, AI, or known-gap AI), index, word count, reliability, verdict (AC-01, AC-08). An analyzer failure line shows the reason instead of an index (AC-09).
3. **False alarms** — human samples above 25, listed separately with name and index (AC-03).
4. **Misses** — ordinary AI samples below 26, with name and index (AC-05).
5. **Errors** — analyzer failures, unclassified samples, bad known-gap entries, missing categories, missing detector copy, each naming the item and the reason (AC-09, 12, 13, 14, 15, 18).
6. **Known-gap list** — every known-gap sample with its reason, so each excused sample is visible (AC-07).
7. **Notes** — drift warnings above 15 up to 25 (AC-04), «gap may be closed» for a known-gap sample at 26 or above (AC-06), hidden-character notes using the analyzer's own invisible-character set, plus an unexpected-encoding note for a sample that is not valid UTF-8 (sad §8 Encoding), the inconclusive mark (AC-08). Notes never change the exit code (AC-19).
8. **Summary** — per-category counts, ignored items, and the sum check against the folder total (AC-12, AC-17), how many ordinary AI samples reach 51 for information (AC-02), how many human samples reach 150 words out of how many (AC-08), the duration, and the verdict line (AC-01).

A failing run still prints the whole report. The report is the same for success and failure except for the failure sections.

## 5. Exit codes

| Code | Meaning | Source |
|---|---|---|
| `0` | Nothing failed. Notes and warnings may be present | AC-01, AC-16, AC-19 |
| `1` | Anything else: analyzer failure, false alarm, miss, unclassified item, bad known-gap entry, missing category, missing detector copy, invalid command line, unhandled runner error (printed as `error eval.runner_error` followed by `result: failed`) | AC-03, 05, 09, 12–15, 18, ADR-0002 |

Only 0 and 1 are used. A consumer reads the code and never needs the report (AC-16). The code cannot tell a detector failure from a broken runner or input; the report says which (ADR-0002, Consequences).

## 6. Failure kinds

There is no error registry in the repo, so these names are this contract's proposal, in the neutral `module.error_name` form, used as labels in the report:

| Kind | Raised when | AC |
|---|---|---|
| `eval.analyzer_failure` | crash, timeout, empty, unreadable or incomplete result, index outside 0 to 100; the reason is in the line | AC-09 |
| `eval.false_alarm` | human sample above 25 | AC-03 |
| `eval.miss` | ordinary AI sample below 26 | AC-05 |
| `eval.unclassified_sample` | plain text file with neither prefix, or a `.txt` extension in the wrong case | AC-12 |
| `eval.bad_known_gap` | entry names a missing sample or a human sample | AC-13, AC-14 |
| `eval.missing_category` | no samples, no human samples or no AI samples | AC-15 |
| `eval.missing_detector_copy` | the named plugin has no `analyze.py` | AC-18 |
| `eval.runner_error` | unhandled exception in the runner | ADR-0002 |

## 7. Examples (placeholder data)

```
$ python evals/run_eval.py
plugin: ukr-text-guard
human-example-one   human   index 12   words 160   reliability high   passed
ai-example-one      AI      index 58   words 210   reliability high   passed
...
summary: 2 human, 8 AI, 0 ignored, 10 of 10 items
human samples with 150 words or more: 1 of 2, human conclusion inconclusive
duration 1.1 s
result: passed
$ echo $?
0
```

```
$ python evals/run_eval.py --plugin ukr-text-unknown
plugin: ukr-text-unknown
error eval.missing_detector_copy: no detector copy exists for plugin ukr-text-unknown
result: failed
$ echo $?
1
```
