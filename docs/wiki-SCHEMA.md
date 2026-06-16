# The research wiki format

dig-deep can read from — and, when you let it, grow — a per-repo research wiki: a
plain-Markdown knowledge store of what prior research runs have synthesized. It's
**entirely optional**. Repos without one work fine (the `wiki` lane returns
`no_wiki: true` and orchestrators skip it).

The point: every dig that writes back makes the next dig warmer. Phase 0 prefetch
saves query budget; writeback is what compounds.

## Layout

```
<repo>/.claude/wiki/
├── SCHEMA.md                     # human-facing copy of these conventions
├── index.md                      # tag-prefixed catalog, one line per page
├── log/YYYY-MM.md                # append-only history of writebacks
├── glossary/
│   ├── _aliases.yaml             # term string → home domain
│   └── <domain>.yaml             # per-domain jargon graph
└── pages/<primary-tag>/<topic>.md
```

## Pages

`pages/<primary-tag>/<topic>.md`. Frontmatter:

```yaml
---
title: <topic>
tags: [tag1, tag2]
sources: [<url>, <DOI/arXiv>, <r/sub thread>, …]   # merged + deduped
last_verified: 2026-06-16
confidence: high        # high | medium | contested | low
---
```

- `high` — all lanes agreed
- `medium` — weak dissent
- `contested` — strong unresolved disagreement
- `low` — thin, single-source

Body sections: `## Summary`, `## Key claims` (inline attribution),
`## Contradictions` (only when lanes disagreed), `## See also` (wikilinks). The
`wiki` lane reads **only** `## Summary` and `## Contradictions` (plus
frontmatter) — keep those self-contained.

## Glossary

`glossary/<primary-tag>.yaml`, one entry per jargon term:

```yaml
gguf:
  definition: A binary container format for quantized LLM weights.
  domain: llm-inference
  aliases: [GGUF]
  related: [llama.cpp, quantization]
  pages: [pages/llm-inference/quantization.md]
  first_seen: 2026-06-16
```

Re-upsert rules: last-writer-wins on `definition`, preserve `first_seen`, merge
`related` and `pages` as sets. Mirror new terms into `glossary/_aliases.yaml`
(`term: home-domain`).

## Index

`index.md`, one line per page:

```
#tag1 #tag2 — [topic-name](pages/<primary-tag>/<topic>.md) — one-line hook
```

The `wiki` lane greps this first to find candidate pages and matching glossary
domains, so keep the tags and hook meaningful.

## Log

`log/YYYY-MM.md`, append-only:

```
## [2026-06-16] writeback — <question>
- created pages/llm-inference/quantization.md
- upserted glossary: gguf, exl2
```

## Reading vs. writing

- **Reading** is always safe and free: `digdeep wiki "<question>"` (the `dig-wiki`
  agent) is strictly read-only.
- **Writing** is a deliberate, user-gated step performed by the **orchestrator**
  (e.g. `dig-deep` Phase 4.5 in the Claude Code adapter), never by the `digdeep`
  CLI. The orchestrator asks for confirmation, then writes only under
  `.claude/wiki/`. If the directory doesn't exist yet, the first approved
  writeback bootstraps the scaffold above (including this `SCHEMA.md`).
