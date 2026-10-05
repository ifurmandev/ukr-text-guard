# api-sync-report — shared-detector

Contract form: `contracts/cli.md` (`target_surfaces: [cli]`; no HTTP surface, so no `openapi.yaml`; no async flow, so no `events.md`).
`data-model.md` absent — legal fast-lane skip: the feature has no datastore and no schema change (sad §2, §6 flags). The contract is derived from the files the tooling reads (sad §5, ADR-0003) in place of a model.
Size: S (`.size`), route `quick`.

## A. Field-origins

| schema_path | origin | confidence |
|---|---|---|
| command `check` / `sync` | sad §4 choice 1, §1 intent; spec US-02, US-03 | high |
| flag `check --staged` | sad §4 choice 4, ADR-0001; spec AC-08 | high |
| carry.json shape `{path: [plugin]}` | ADR-0003; sad §5 | high |
| shared file set (5 paths) | sad §5; spec §1 | high |
| finding line `error shared.<code>: <file> <plugin> <detail>` | sad §8 Report format (mirrors `evals/run_eval.py` `error eval.*`) | high |
| codes `differing, line_endings, missing, unlisted, orphan_source, carry_entry, cannot_run` | sad §8 | high |
| final line `result: passed\|failed` | sad §2 Conventions; `evals/run_eval.py:302` | high |
| exit codes 0 / 3 / 4 | sad §4 choice 3, §8 | high |
| overwrite notice wording | sad §8 + spec AC-05 (meaning fixed, wording proposed) | medium |
| success line `checked N files in M plugins` | spec AC-04 (content fixed), line format proposed | medium |
| sync lines `rewrote` / `created` / `left in place, delete by hand` / `all copies are up to date` | spec AC-01, AC-02, AC-03b (content fixed), line format proposed | medium |
| repository root = parent of `tools/` | analogy to `evals/run.sh` `here`; not stated in sad | low |
| usage error → exit 4 | sad §8 «any unexpected exception → 4»; usage case inferred | low |
| `invisible mark` reported as `shared.differing` | no code in sad §8 | low |

## B. Drift findings

Forward and back-feed checks; the interface kind has no database and no HTTP endpoints, so points 1 and 3 are applied to the files the command reads.

| # | Point | Result | Note |
|---|---|---|---|
| 1 | Command ↔ model *(core)* | ✓ | every command reads/writes only the files of sad §5 (shared source, carry list, plugin copies, Git index); `check` never writes |
| 2 | Error code ↔ repo definition *(core)* | ✓ | no error registry exists for `shared.*`; the eval runner prints `eval.*` codes inline as strings, the same form. `shared.*` codes are the contract's proposal from sad §8 |
| 3 | Validation ↔ constraint *(core)* | ✓ | path rules (relative, forward slashes, inside plugin folder) match sad §8 «Paths and bytes» and spec AC-03 |
| 4 | Contract ↔ sequence *(supporting)* | ✗ → F2 | see flags |

Back-feed coverage:

- Every AC maps to a command or is N/A: AC-01..06, 08, 08b, 10, 12 → contract; AC-07 → *Callers* (`run.sh`); AC-09, 11, 13, 14 → N/A, non-runtime. ✓
- Every command maps to a user story: `sync` → US-01, US-02, US-06; `check` → US-03, US-04, US-05, US-06; US-07 non-runtime. ✓
- Every `alt` branch of flows 1–4 has an outcome in the contract. Flow 1 lacks one branch that the contract needs → F2.

## Flags (4) and resolution

| # | Flag | Resolution |
|---|---|---|
| F1 | Sequence/design gap: flow 4 and AC-12 name «line endings or an invisible mark», but sad §8 has the code `shared.line_endings` only. | **Accept** in the contract: an invisible-mark-only difference is `shared.differing` with the detail saying so. **Save-as-OQ** → OQ-1, owner `design` (sad §8), due before the contract is finalized |
| F2 | Sequence gap: flow 1 (sync) has no «could not run» branch, though sad §8 gives `sync` exit 4. | **Save-as-OQ** → OQ-2, owner `sequences` (sad §6 flow 1), due before the contract is finalized. The contract already carries exit 4 for `sync` |
| F3 | Repository root is not stated in the SAD. | **Accept**: parent of `tools/`, as `run.sh` locates its own folder. No flag, no environment variable |
| F4 | Exact text of the success and sync lines is not fixed upstream (only their content). | **Accept** as the contract's proposal; the unit tests of `tools/tests/test_shared_sync.py` will pin the text |

## Open questions raised

- **OQ-1** — Should an invisible-mark-only difference get its own code (for example `shared.invisible_mark`), or stay `shared.differing`? Owner: `design` (Ihor Furman), due: before the contract is finalized.
- **OQ-2** — Add the «check could not run» branch (exit 4, `shared.cannot_run`) to sad §6 flow 1 (sync). Owner: `sequences` (Ihor Furman), due: before the contract is finalized.

The four open questions already in spec §8 and sad §11 (deleting unlisted files, plugin versions, direct runner check, pinning line endings) are unchanged; this contract follows their stated defaults.

## Lint

No OpenAPI document, so `spectral` does not apply. The checkable form of this contract is the unit tests planned in sad §10 (one per divergence kind, exit codes 3 and 4 for `evals/run.sh`).
