# Tracker — ukr-text-eval

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Add the pure judging function and the band constants | domain | Ihor Furman | S | — | done |
| T2 | Discover and classify the items of the sample folder | infra | Ihor Furman | S | — | done |
| T3 | Read and validate the known-gap list, seed it with the first entry | infra | Ihor Furman | S | T2 | done |
| T4 | Analyse one sample in a fresh process and fail closed | infra | Ihor Furman | M | — | done |
| T5 | Build the report, the evidence summary and the outcome decision | app | Ihor Furman | M | T1, T2, T3, T4 | done |
| T6 | Add the CLI entry point, detector copy lookup and exit code | ports | Ihor Furman | S | T5 | done |
| T7 | Make run.sh a thin delegate that finds a working Python | wiring | Ihor Furman | S | T6 | done |
| T8 | Prove independence and repeatability on the real analyzer | tests | Ihor Furman | S | T6 | done |
| T9 | Verify the first real run on both shells and update the docs | docs | Ihor Furman | S | T7, T8 | done |

**Total:** 9 tasks, ~6 person-days (7 × S at about 0.5 day, 2 × M at about 1 day).
