# dig-deep — Claude Code adapter

A complete, working rendering of the `AGENTS.md` spec for [Claude
Code](https://claude.com/claude-code). These are the same six `dig-*` agents the
project's friends already use — refactored so the heavy lifting lives in the
portable `digdeep` CLI and the agent files are thin orchestration prompts.

## What's here

| Agent | Role |
|-------|------|
| `dig-deep` | Orchestrator — broad web sweep, parallel fan-out, synthesis (uses the Agent tool) |
| `dig-meta` | Web lane — `digdeep web` |
| `dig-reddit` | Reddit lane — `digdeep reddit` |
| `dig-papers` | Papers lane — `digdeep papers` |
| `dig-yt` | YouTube lane — `digdeep youtube` |
| `dig-wiki` | Read-only wiki lookup — `digdeep wiki` |

The lane agents must be present as **agents** (not just skills) because
`dig-deep` fans out to them via `subagent_type`.

## Install

Two transparent steps — no script to run, just commands you can read first.

**1. Install the `digdeep` CLI:**

```bash
pip install digdeep        # or: pipx install digdeep
```

**2. Copy the six agents into your Claude Code agents directory:**

```bash
cp adapters/claude-code/agents/*.md ~/.claude/agents/
```

Prefer symlinks, so a later `git pull` updates them in place? From the repo root:

```bash
for f in "$PWD"/adapters/claude-code/agents/*.md; do ln -sf "$f" ~/.claude/agents/; done
```

Then check the dependencies:

```bash
digdeep doctor
```

`ddgs` and `yt-dlp` are required (for the web and YouTube/playlist lanes);
`playwright` and `trafilatura` are optional. `digdeep doctor` prints the exact
install command for anything missing.

## Use

In Claude Code:

```
> use dig-deep to research: what's the best split keyboard for RSI in 2026?
```

or invoke a single lane directly (e.g. "use dig-reddit to …"). The orchestrator
honors an optional soft time budget in the question ("quick dive", "~10 min",
default: take your time).

## Customize

These files are a starting point — copy and edit them. To change the workflow
itself (routing, budgets, output shape), edit `dig-deep.md`; the lane agents just
wrap `digdeep` commands. For a non-Claude-Code framework, start from the
framework-neutral [`AGENTS.md`](../../AGENTS.md) instead.
