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

1. If `no_wiki`, skip the lane. When it also returns `foreign_wiki: true`, a
   `.claude/wiki/` exists but isn't in the dig-deep schema — read those files
   directly with Read/Grep instead.
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

**Only the dig-deep schema is supported.** A `.claude/wiki/` with none of the
structural markers (a `SCHEMA.md`, a `glossary/` dir, or a `pages/` dir) is treated
as foreign (`foreign_wiki: true`) and
handed off for direct reading. Full glossary-subgraph traversal (following
`related:` edges, resolving `_aliases.yaml`) needs the optional `[wiki]` extra
(`pip install 'digdeep[wiki]'`, PyYAML); without it the glossary degrades to a
substring scan.
