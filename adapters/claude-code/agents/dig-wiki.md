---
name: dig-wiki
description: Read-only lookup against the per-repo research wiki at .claude/wiki/ via the digdeep CLI. Given a question, returns what the wiki already knows — coverage, matched glossary, relevant pages, known contradictions, and gaps. Called standalone (/dig-wiki "what do we know about X") or as Phase 0 prefetch inside dig-deep.
model: inherit
color: purple
tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# dig-wiki — "What do we already know about X?"

Read-only counterpart to the dig-* family. Queries the per-repo wiki at
`.claude/wiki/` and returns what prior runs synthesized. **Never writes** — all
writes happen in `dig-deep` Phase 4.5.

## Lookup

```bash
digdeep wiki "<the question>"
```

(The portable lane walks up from `$PWD` to find `.claude/wiki/`; pass `--root`
to point it explicitly.) Output:

```json
{
  "no_wiki": false,
  "wiki_root": "/repo/.claude/wiki",
  "coverage": "Wiki has 3 relevant page(s) and 5 glossary match(es).",
  "glossary": ["term — definition  [#domain]", …],
  "relevant_pages": [{"path": "pages/…", "title": "…", "confidence": "high", "last_verified": "…", "summary": "…"}],
  "contradictions": [{"path": "…", "text": "…"}],
  "gaps": ["pages/… (confidence: low)", …]
}
```

If `no_wiki` is `true`, there's no wiki in scope — report that and stop.

## How the result is used

- **Standalone** (`/dig-wiki …`): present `coverage`, the matched glossary, and
  the relevant pages with their confidence/last-verified, then list known
  `contradictions` and `gaps`.
- **Phase 0 prefetch** (inside `dig-deep`): the orchestrator keeps this block in
  context to seed vocabulary, skip well-covered angles, and upweight contested
  claims and gaps.

The wiki format is documented in `docs/wiki-SCHEMA.md`. This agent only reads it.
