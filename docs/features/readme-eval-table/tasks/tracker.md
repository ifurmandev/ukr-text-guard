# Tracker — readme-eval-table

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Run the eval on the ukr-text-guard copy and gate on run-level failure | docs | Ihor Furman | S | — | done |
| T2 | Replace the README sample table with the eval table header and rows | docs | Ihor Furman | S | T1 | done |
| T3 | Fill the result cells with the six-value mapping, known-gap and failed rows | docs | Ihor Furman | M | T2 | done |
| T4 | Add the caption, the evidence note and the pointer to the honest-limit section | docs | Ihor Furman | S | T1 | done |
| T5 | Compare the table with the report and prepare the pull request | docs | Ihor Furman | S | T3, T4 | review |

**Total:** 5 tasks, ~1 person-day (one PR).
