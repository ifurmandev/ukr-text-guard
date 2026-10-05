# Tracker — shared-detector

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Seed shared/, carry.json, .gitattributes | infra | Ihor Furman | S | — | done |
| T2 | Plan core: reader interface, carry validation, comparator | domain | Ihor Furman | M | — | done |
| T3 | `check` command, report, exit codes 0/3/4 | ports | Ihor Furman | M | T1, T2 | done |
| T4 | `sync` command | app | Ihor Furman | M | T2, T3 | done |
| T5 | Git index reader, `check --staged` | infra | Ihor Furman | M | T3 | done |
| T6 | `.githooks/pre-commit` | wiring | Ihor Furman | S | T5 | done |
| T7 | `evals/run.sh` runs the check first | wiring | Ihor Furman | S | T3 | done |
| T8 | README + architecture map | docs | Ihor Furman | S | T4, T6, T7 | todo |
| T9 | Acceptance run | tests | Ihor Furman | S | T1, T4, T7, T8 | todo |

**Total:** 9 tasks, ~6 person-days (4 × M ≈ 1 day each, 5 × S ≈ 0.5 day each).
