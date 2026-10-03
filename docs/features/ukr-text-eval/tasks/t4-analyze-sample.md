---
id: T4
title: "Analyse one sample in a fresh process and fail closed"
layer: "infra"
deps: []
blocks: ["T5"]
acs: ["AC-09", "AC-10"]
files_hint: ["evals/run_eval.py", "evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "M"
context_budget: "M"
status: "done"
---

# T4 — Analyse one sample in a fresh process and fail closed

## Place in the sequence

- **Blocked by:** none (logically independent; physically after T1, which creates the file) · **Blocks:** T5 — Build the report and the outcome · **Wave:** 1 by dependency, runs after T1–T3 in its lane.
- **Lane:** shares `evals/run_eval.py` and `evals/tests/test_run_eval.py` with T1, T2, T3, T5, T6, T8 — serialized.

## Why (user story)

> **As a** plugin author
> **I want** an analyzer failure counted as a failure, never as a low index
> **So that** a broken detector copy cannot look like a clean human text.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task delivers the per-sample function that talks to the detector copy and turns every unusable answer into a `Failure` with a reason.

## Inlined context

> **Flow: analyse one sample and fail closed.** Read the sample as bytes, decode as UTF-8 with replacement and scan for a byte-order mark or invisible characters. Start a fresh process with UTF-8 forced and a 10 second limit. Branches: no result within 10 seconds → stop the process, failure «timed out» · process crashed or exited with an error → «crashed» · empty output → «empty result» · output cannot be read as a result → «unreadable result» · index or reliability missing → «incomplete result» · index outside 0 to 100 → «index out of range» · usable result → index, word count and reliability. Nothing is kept for the next sample.
>
> — `sad.md §6, «Flow: analyse one sample and fail closed», abridged` · full text: [sad.md](../sad.md)

> **Decision override:** the runner starts the analyzer with `sys.executable` and `PYTHONUTF8=1`, unlike the documented `python3 scripts/analyze.py FILE`. On the author's Windows machine `python3` is a Microsoft Store stub, and piped analyzer output is otherwise in the console encoding.
>
> — `sad.md §1, Decision override, abridged` · full text: [sad.md](../sad.md)

> **Analyzer is a black box with a fixed CLI:** `analyze.py FILE --json` prints a JSON object with Ukrainian keys `індекс`, `надійність_статистики` and `метрики.слів`. The runner may not change the copies.
>
> — `sad.md §2, Technical, abridged` · full text: [sad.md](../sad.md)

> **Hard rule (Portability and Encoding):** the child is started with an argument list and no shell; its stdout is decoded as UTF-8 bytes; the interpreter is `sys.executable`.
>
> — `sad.md §8, Portability and Encoding, abridged` · full text: [sad.md](../sad.md)

> **Hard rule (NFR):** a sample that gets no result within 10 s is an analyzer failure; each sample's verdict is identical alone, together and in reverse order.
>
> — `spec.md §6, Time limit per sample and Independence of samples, abridged` · full text: [spec.md](../spec.md)

Checked on disk (`analyze.py:505-513`): `надійність_статистики` is a Ukrainian text string (for example «низька (текст закороткий)») and `індекс` is capped by `min(100, score)`. Check the real JSON of one sample once to confirm `індекс` and `метрики.слів` are integers, then validate exactly that type (a boolean or a string is never accepted). The word count is taken from the analyzer, never recounted. The hidden-character scan result is returned with the analysis so T5 can print its note (spec §8 OQ-3 default). Failure kind: `eval.analyzer_failure` with the reason in the line.

**Fallback:** insufficient or contradicted by the code → read [sad.md](../sad.md) §6, §8 and the `analyze.py` entry point in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. The detector's JSON keys are the only external shape: see [cli.md](../contracts/cli.md) §3 (Detector copy).

## Acceptance criteria

### AC-09 — error

> **Given** the analyzer crashes for a sample, returns an empty or unreadable result, leaves out the index or the reliability, returns an index outside 0 to 100, or gives no result within 10 seconds
> **When** the plugin author runs the check
> **Then** that sample is reported as an analyzer failure with the reason, counted as failed, and never shown as a low index
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

### AC-10 — domain invariant: samples do not affect each other

> **Given** the same samples
> **When** the plugin author runs them alone or together with others in any order
> **Then** each sample receives the same index and the same verdict
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `analyze_sample(analyzer_path, sample_path) -> Analysis | Failure` (plus a hidden-character flag) in `evals/run_eval.py`: `subprocess.run([sys.executable, analyzer, sample, "--json"], env with PYTHONUTF8=1, capture_output, timeout=SAMPLE_TIMEOUT_S)`, no shell.
- [ ] Map each failure branch to a distinct `Failure.reason` as listed above; validate index is an integer in 0..100 and reliability is a non-empty string.
- [ ] Add the byte-order mark and invisible-character scan (zero-width, byte-order mark) over the decoded sample text.
- [ ] Tests in `evals/tests/test_run_eval.py` using fake analyzer scripts written to a temporary folder: crash, sleep past the limit (patch the limit to 1 s), empty output, non-JSON, missing key, index 101 and -1, valid result.

## Edge cases

| Case | Behaviour |
|---|---|
| Analyzer sleeps past the limit | process stopped, `Failure("timed out")` |
| Non-zero exit code | `Failure("crashed")` with the exit code and the last stderr line |
| Empty file (the real analyzer raises `ValueError`) | counted as `crashed`, never a low index |
| Output not JSON | `Failure("unreadable result")` |
| JSON without `індекс` or `надійність_статистика` | `Failure("incomplete result")` |
| Index 100 / 0 | accepted; 101 or -1 → `Failure("index out of range")` |
| Index is a string or a boolean | `Failure("unreadable result")`, not coerced |
| Sample with a byte-order mark | analysed normally, hidden-character flag set |

## Definition of Done

- [ ] Each failure branch has a fake-analyzer test that asserts a `Failure` and its reason.
- [ ] A fake analyzer that sleeps past the limit finishes the test run within a few seconds and is reported as timed out.
- [ ] Two calls on the same sample return equal results (state does not leak).
- [ ] Every Hard Rule inlined above still holds (no shell, `sys.executable`, UTF-8 both ends).
