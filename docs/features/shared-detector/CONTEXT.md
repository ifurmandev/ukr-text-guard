---
status: Living
updated_at: "2026-10-04"
---

# Domain Context — shared-detector

<!--
CONTEXT.md is the domain glossary — not a spec and not a scratch pad. NO implementation
detail here (no datastore/broker/framework names, no API contracts) — only domain words
and the boundaries between them. Implementation choices live in the SAD and ADRs; behaviour
lives in spec.md.
-->

## Glossary

- Carry list — the list that says which plugins carry which shared file. NOT what a plugin actually holds on disk; a difference between the two is a divergence.
- Divergence — a plugin copy that differs from the shared source, or is missing although the carry list requires it, or a file a plugin holds at the path of a shared file that the carry list does not give it. NOT a false alarm and NOT a band failure of the eval.
- Divergence check — the check that fails when any divergence exists and names each file and plugin. NOT the eval, which judges samples against bands and says nothing about whether plugin copies are equal.
- Plugin copy — the physical copy of a shared file inside one plugin, the one an installed plugin reads. NOT the shared source; the detector copy of the root glossary is the plugin copy of the analyzer file.
- Shared file — a file that several plugins carry with identical content. NOT the skill description file, which differs in every plugin.
- Shared source — the one editable reference version of the shared files, from which every plugin copy is made. NOT a plugin copy; nothing installed reads it.
- Sync — rewriting every diverged plugin copy from the shared source and listing what was rewritten. NOT the divergence check, which only reports and never changes a file.
