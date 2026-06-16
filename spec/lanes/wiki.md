# Lane: wiki — "what do we already know?"

`digdeep wiki` is a **read-only** lookup against a per-repo research wiki at
`.claude/wiki/`. It answers what prior research runs have already synthesized, so
a new dig can skip well-covered ground and focus on gaps. It never writes.

## Command

```
digdeep wiki "<question>" [--root /path/to/.claude/wiki]
```

Walks up from the current directory to find `.claude/wiki/` (or use `--root`).
Returns `{no_wiki, wiki_root, coverage, glossary, relevant_pages, contradictions, gaps}`.
If there's no wiki in scope, `no_wiki` is `true` — just skip the lane.

## How to use it

Run it as **Phase 0**, before the web sweep:

1. If `no_wiki`, skip — the wiki is out of scope or cold.
2. Otherwise, fold the result into the dig:
   - **Reuse the `glossary` vocabulary** in your search queries.
   - **Skip angles** already covered by high-confidence pages.
   - **Upweight `contradictions` / `gaps`** — those are exactly where fresh
     evidence is most valuable.

## The wiki format

The wiki is a plain-Markdown knowledge store (`index.md`, `glossary/<domain>.yaml`,
`pages/<tag>/<topic>.md`) — see [`docs/wiki-SCHEMA.md`](../../docs/wiki-SCHEMA.md).
It's optional: most repos won't have one, and the lane degrades cleanly to
`no_wiki`. Writeback (growing the wiki after a dig) is a deliberate, user-gated
step the orchestrator does directly — never the CLI.
