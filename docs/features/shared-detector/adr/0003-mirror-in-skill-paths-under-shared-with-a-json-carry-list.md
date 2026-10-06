---
status: Accepted
owner: "Ihor Furman"
reviewers: []
updated_at: "2026-10-05"
feature_size: "S"
ticket: ""
---

# 0003 — Mirror the in-skill paths under `shared/` and list the carriers in `shared/carry.json`

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** Ihor Furman (plugin author), Claude (architect, during the design walk)

## Context

The shared source needs a place and a shape, and the carry list (which plugin carries which shared file) needs a form. Both are read by the sync, by the check, by their tests and by the plugin author in the README, so the format is a contract between several modules. The roadmap already names a new `shared/` folder as the zone of this step.

## Decision drivers

- AC-03, AC-03c: a carry list entry that names a missing file, a missing plugin or a path outside a plugin folder is reported by name.
- AC-06: an unlisted copy is judged only by the path of a shared file, so the path of a shared file has to be derivable without a lookup table.
- AC-14: no file is added to, removed from or moved in any plugin folder.
- US-05: the plugin author can read in one place who carries what.
- §2: standard library only, so the carry list is read with the standard library on any Python 3.

## Considered options

1. **`shared/` mirrors the in-skill paths, and `shared/carry.json` maps each shared path to the plugins that carry it** — for example `shared/scripts/analyze.py` is copied to `plugins/<p>/skills/<p>/scripts/analyze.py` for every plugin `<p>` listed under `scripts/analyze.py`.
2. **`shared/` mirrors the in-skill paths, and the carry list is a constant inside the Python script** — no separate data file.

A per-plugin manifest kept inside each plugin folder was dropped at once: it would add a file to every plugin, which AC-14 forbids.

## Decision outcome

**Chosen:** Option 1. The carry list is data, not code: the author changes it without touching logic, the tests feed their own list, and the list sits next to the files it describes. Mirrored paths remove any translation table between a name in the source and a path in a plugin.

## Consequences

**Positive**
- Adding a shared file is two steps (put it under `shared/`, add its entry); the check fails with «file that no plugin carries» if the second step is forgotten.
- The carry list can be read and tested without running the script.

**Negative**
- JSON has no comments, so the reasons for a carry decision live in the README, not next to the entry.
- `carry.json` is the only file under `shared/` that is not a shared file; the check excludes it by its fixed name.

**Neutral**
- Moving the list into the script (option 2) or a different format later costs about a day: the reader function and the tests change, the plan logic does not.

## Links

- Spec: [[../spec.md]]
- SAD: [[../sad.md]] §4
- Related ADR: [[0001-read-staged-content-from-the-git-index]]
