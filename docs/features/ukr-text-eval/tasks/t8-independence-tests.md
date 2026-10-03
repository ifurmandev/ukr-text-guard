---
id: T8
title: "Prove independence and repeatability on the real analyzer"
layer: "tests"
deps: ["T6"]
blocks: ["T9"]
acs: ["AC-10"]
files_hint: ["evals/tests/test_run_eval.py"]
owner: "Ihor Furman"
estimate: "S"
context_budget: "M"
status: "done"
---

# T8 — Prove independence and repeatability on the real analyzer

## Place in the sequence

- **Blocked by:** T6 — CLI entry point, detector copy lookup and exit code · **Blocks:** T9 — Verify the first real run on both shells and update the docs · **Wave:** 5, runs in parallel with T7 in time, but shares the test file with T1–T6, so it follows them in that lane.
- **Lane:** shares `evals/tests/test_run_eval.py` with T1–T6 — serialized after them; independent of T7.

## Why (user story)

> **As a** plugin author
> **I want** an analyzer failure counted as a failure, never as a low index
> **So that** a broken detector copy cannot look like a clean human text.
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task delivers the release check for «each sample's verdict is the same alone, together and in reverse order», run against the real detector copy and the real samples, which the fake-analyzer unit tests cannot show.

## Inlined context

> **QG-1. Verdict integrity — how to verify:** a unit test imports the runner and calls the per-sample function on the real samples and the real analyzer copy in three orders (alone, together, reverse), comparing verdicts — this is the «comparison of the three runs before release» of spec §6, without an order flag in the CLI; a diff of two consecutive reports differs only in the duration line.
>
> — `sad.md §10, QG-1, abridged` · full text: [sad.md](../sad.md)

> **NFR Repeatability:** two consecutive runs on the same inputs give identical indexes and verdicts, 100%. **NFR Independence of samples:** each sample's verdict is identical when it is run alone, together with the others, and in reverse order, 100%.
>
> — `spec.md §6, Repeatability and Independence of samples, abridged` · full text: [spec.md](../spec.md)

> **Hard rule (Determinism):** the per-sample path is an importable function, so the independence check runs against the real analyzer copy and the real samples in three orders; the CLI has no order flag.
>
> — `sad.md §8, Determinism, abridged` · full text: [sad.md](../sad.md)

Uses T4 `analyze_sample()` and T1 `judge()` on `plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py` and `evals/samples/*.txt`. The test never asserts that the real samples pass their bands (that is T9's first-run observation); it asserts only that verdicts agree across orders and runs.

**Fallback:** insufficient or contradicted by the code → read [sad.md](../sad.md) §8, §10 and [spec.md](../spec.md) §6 in full. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-10 — domain invariant: samples do not affect each other

> **Given** the same samples
> **When** the plugin author runs them alone or together with others in any order
> **Then** each sample receives the same index and the same verdict
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add a test class in `evals/tests/test_run_eval.py` that, for every real sample, collects `(index, verdict)` alone, in sorted order together and in reverse order, and asserts equality per sample.
- [ ] Add a test that runs `run_check` twice on the real folder and asserts the two reports are equal after removing the duration line.
- [ ] Skip, with a clear message, only when the real detector copy is absent in the checkout.

## Edge cases

| Case | Behaviour |
|---|---|
| A sample's index changes with order | test fails, naming the sample and both indexes |
| Real analyzer unavailable (copy missing) | test is skipped with a message, never reported as passed silently |
| Duration line differs between the two reports | ignored by the comparison; any other difference fails the test |
| A sample fails as `eval.analyzer_failure` in all three orders | still equal, test passes (failure is a stable verdict) |

## Definition of Done

- [ ] `python -m unittest discover evals/tests` passes on the real folder with the three-order and two-run tests included.
- [ ] The three-order comparison covers all samples currently in `evals/samples/`.
- [ ] The test never edits the samples, the analyzer or the bands.
