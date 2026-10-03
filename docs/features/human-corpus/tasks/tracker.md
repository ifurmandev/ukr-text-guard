# Tracker — human-corpus

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Create the sources register skeleton | docs | Ihor Furman | S | — | done |
| T2 | Select candidates and register the first batch | docs | Ihor Furman | M | T1 | done |
| T3 | Add the sample files and remove the two short ones | docs | Ihor Furman | M | T2 | done |
| T4 | Run the check and verify the verdict | tests | Ihor Furman | S | T3 | done |
| T5 | Refresh the README table and caption | docs | Ihor Furman | S | T4 | done |
| T6 | Write the changelog note on the removed baseline | docs | Ihor Furman | S | T4 | done |

**Total:** 6 tasks, about 3 person-days (the candidate search in T2 is the long pole).
