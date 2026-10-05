---
status: Accepted
owner: "Ihor Furman"
reviewers: []
updated_at: "2026-10-05"
feature_size: "S"
ticket: ""
---

# 0001 — Read the staged content from the Git index in the before-commit check

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** Ihor Furman (plugin author), Claude (architect, during the design walk)

## Context

The before-commit step must judge the content that is about to be committed, not the files left in the working folder (spec AC-08). The two can differ: a copy with a divergence can be staged while the working folder already holds a fixed version, and the other way round. The check core is shared by three entry points (§5), so the way the staged content is read decides the shape of that core and of its tests.

## Decision drivers

- AC-08: the check judges both the shared source and the plugin copies as they are being committed, whatever files the commit touches.
- QG-2 in §1 (safety of writes): the before-commit step must not change the plugin author's working folder.
- Spec §6 NFR: the divergence check takes ≤ 2 s for 5 shared files in 3 plugins.
- Spec AC-12: copies are equal byte for byte, so one byte comparator must serve every source of content.
- §2: standard library only, Git 2.9 or newer.

## Considered options

1. **Read the index directly** — the core works through a tree reader with two implementations behind one interface (list paths, read bytes): one reads the working folder, the other reads the Git index with `git ls-files` and `git cat-file`.
2. **Export the index to a temporary folder** — the hook runs `git checkout-index --prefix=<tmp>/ -a` and runs the ordinary working-folder check on that folder.
3. **Stash what is not staged** — the hook runs `git stash --keep-index`, runs the ordinary working-folder check, and restores the stash.

## Decision outcome

**Chosen:** Option 1. It is the only option that neither copies the repository on every commit (option 2) nor touches the plugin author's working folder (option 3), and the byte comparator stays the same for both readers. The price is a thin layer over Git plumbing, which is tested against a real temporary repository.

## Consequences

**Positive**
- Nothing is copied and no working file is changed; a failed or interrupted hook leaves no debris.
- One comparator and one report format for the working folder and the index; unit tests use an in-memory reader and need no Git.

**Negative**
- The index reader is code that depends on Git plumbing output (`ls-files -z`, `cat-file --batch`) and needs an integration test with a real repository.
- Git converts line endings when it stages (`core.autocrlf`), so the staged content and the working-folder content can differ in line endings; the staged check and the on-demand check can then give different answers for the same copy. Recorded in §11. Mitigated on 2026-10-05 by a committed `.gitattributes` with `eol=lf` for the shared source and the plugin copy paths, so Git does not convert those files.

**Neutral**
- Switching to option 2 later means replacing the index reader with an extraction step; about one day of work.

## Links

- Spec: [[../spec.md]]
- SAD: [[../sad.md]] §4
- Related ADR: [[0002-ship-the-hook-in-githooks-with-core-hookspath]]
