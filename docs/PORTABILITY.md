# Portability — what ports, what doesn't, and how to add an adapter

dig-deep is split so that almost everything is framework-agnostic and the small
framework-specific part is isolated in `adapters/`.

## The three layers

```
scripts/digdeep/   ── portable core: the lanes + CLI. Pure Python + 2 external
                      CLIs (ddgs, yt-dlp). No LLM, no framework. Runs anywhere.
       ▲
AGENTS.md          ── portable spec: the orchestration logic (routing, budgets,
                      round loop, synthesis shape) as framework-neutral prose.
       ▲
adapters/<tool>/   ── the only framework-specific layer: a thin rendering of
                      AGENTS.md for one host (e.g. Claude Code subagents).
```

## What ports cleanly (≈ all of it)

- **The lanes.** They're CLI calls that emit JSON. Anything that can run a shell
  command and parse JSON can use them — an LLM with a shell tool, a Python
  script, a Makefile, a human.
- **The routing table** (which lane for which question).
- **The budget profiles** (Quick / Standard / Deep) — also available in code as
  `digdeep.budgets.PROFILES`.
- **The round loop** (search → triage → follow up on specific leads → stop).
- **The synthesis shape** (findings by sub-question, attribution, direct answer).

None of that depends on Claude Code. It's prose and CLI calls.

## What does *not* port automatically

**Parallel fan-out with isolated context windows.** In Claude Code, Phase 3
launches each lane as a concurrent *subagent*, so:

- lanes run in parallel (faster), and
- each lane's raw, noisy output stays in its own context — only the distilled
  findings come back to the orchestrator, which keeps the main context clean and
  lets a run go deeper than a single context could hold.

On a single-context framework you simply run the lanes **sequentially in one
context**. You get the same routing, the same budgets, and the same final
report — it's just slower and the orchestrator's context carries more raw
material along the way. If your framework *does* offer task spawning
(LangGraph nodes, CrewAI tasks, AutoGen agents, a job queue), map Phase 3 onto
that and you recover the parallelism.

This is the one place an adapter has real work to do. Everything else is copy +
lightly edit.

## Writing a new adapter

1. **Start from `AGENTS.md`.** Copy it into your framework's system-prompt /
   rules / instructions mechanism.
2. **Wire the tool calls.** Wherever the spec says `digdeep <lane> …`, make sure
   your agent can run that shell command (and that `digdeep` is on PATH —
   `pip install digdeep`).
3. **Map Phase 3 to your concurrency model.** Parallel task spawning if you have
   it; otherwise a sequential loop over the chosen lanes.
4. **Keep the synthesis + output format** from the spec; tweak to taste.
5. Drop it in `adapters/<your-framework>/` with a short README and copy-paste
   install commands (prefer plain commands over a script users must trust). PRs welcome.

The [`adapters/claude-code/`](../adapters/claude-code/) directory is a complete
worked example: six agent files where the orchestrator uses native parallel
subagents and each lane agent is a thin wrapper over a `digdeep` command.

## Why no MCP server / hosted service?

By design. A hosted service would mean operating infrastructure (and taking on
the liability/privacy that comes with proxying other people's research queries).
dig-deep deliberately ships only *code*: you install it, it runs locally, it
talks to public endpoints directly. Distribution is a plain git repo (plus PyPI
for convenience). Nothing to host, nothing to trust.
