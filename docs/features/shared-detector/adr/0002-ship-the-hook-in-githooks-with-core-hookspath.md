---
status: Accepted
owner: "Ihor Furman"
reviewers: []
updated_at: "2026-10-05"
feature_size: "S"
ticket: ""
---

# 0002 — Ship the before-commit hook in a committed `.githooks` folder activated through `core.hooksPath`

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** Ihor Furman (plugin author), Claude (architect, during the design walk)

## Context

Git does not clone hooks together with a repository, so the before-commit step reaches a fresh clone only through a setup action by the plugin author. The spec allows exactly one such setup per clone, described in the README (AC-09), and states that without it only the on-demand check and the eval entry point protect. The choice decides how many steps the author takes, whether the installed hook can go stale, and whether a dependency is added.

## Decision drivers

- AC-09: one-time setup per clone, named in the README together with its limit.
- AC-08b: when the check cannot run, the commit is refused with a message; the hook therefore has to be a script the repository controls.
- §2: no dependency manifest and no package install in the repository; Bash and Git 2.9 or newer are assumed.
- The abuse case «setup never done» in spec §6.1: a hook copy that silently goes stale is worse than a hook that is simply absent.

## Considered options

1. **Committed `.githooks/pre-commit` plus `git config core.hooksPath .githooks`** — the hook is a file in the repository; the one-time setup is one command.
2. **An installer script that copies the hook into `.git/hooks/`** — the repository holds a hook template and an `install` command.
3. **The `pre-commit` framework** — a `.pre-commit-config.yaml` plus `pre-commit install`, with the framework installed from PyPI.

## Decision outcome

**Chosen:** Option 1. The hook that runs is always the committed file, so it cannot go stale on a clone, and the setup is one command with no dependency. Option 2 leaves a frozen copy per clone, and option 3 adds a package install and its own stash of unstaged changes, which brings back the risk rejected in ADR-0001.

## Consequences

**Positive**
- One command of setup; a change to the hook reaches every set-up clone with the next pull.
- No new dependency; the hook is a short Bash script that probes the same interpreters as `evals/run.sh`.

**Negative**
- `core.hooksPath` replaces the whole hooks folder of that clone, so any other hook kept in `.git/hooks/` stops running.
- On Linux and macOS the hook file must be committed with the executable bit (`git update-index --chmod=+x`).

**Neutral**
- Moving to option 2 or 3 later changes the README setup text and one file; no effect on the check itself.

## Links

- Spec: [[../spec.md]]
- SAD: [[../sad.md]] §4
- Related ADR: [[0001-read-staged-content-from-the-git-index]]
