# Ports: the same graph on Claude Code, Codex and Kiro Crew, mostly in markdown

`run.py` is a stand-in harness. Your real harness already has a loop runner, subagents, skills and hooks, so the graph can be mostly markdown there. The five primitives line up one to one:

| Primitive | What it carries here | Claude Code | Codex | Kiro Crew / Kiro CLI |
|---|---|---|---|---|
| Instructions file | the self-improvement loop rules | `CLAUDE.md` | `AGENTS.md` | `.kiro/steering/todo-graph.md` |
| Agent definitions | who may do what (tool sets, model) | `.claude/agents/*.md` (frontmatter `tools`, `model`) | `.codex/agents/*.toml` (`name`, `description`, `developer_instructions`, `model`) | `.kiro/agents/*.json` (`tools`, `allowedTools`, `hooks`) |
| Skill | the graph itself, as numbered nodes | `.claude/skills/run-issue/SKILL.md` | `.codex/skills/run-issue/SKILL.md` | linked into `~/.kiro/crew/skills/` |
| Hooks | the hard edges: tests after every edit, no stopping while red | `.claude/settings.json` `PostToolUse` + `Stop`, exit 2 blocks | `.codex/hooks.json` same events, exit 2 blocks, trust once via `/hooks` | `postToolUse` on the coder agent JSON; verify/stop stays in the skill (Kiro CLI hook event names TO BE CONFIRMED against your build) |
| Headless run | the outer loop nobody prompts | `claude -p "..."` in `loop.sh` | `codex exec --full-auto "..."` in `loop.sh` | `cron_add` + `spawn_run(agent=...)` |

Shared across all three (`ports/shared/`): the two skills, `verify.sh`, the two hook scripts, `validate_proposal.py`, and a `lessons.md` template. Only the thin wiring differs per harness.

## Install into your checkout

```bash
git clone git@github.com:ivikash/todo-graph-demo.git && cd todo-graph-demo
bash ports/install.sh claude-code     # or: codex | kiro-crew
```

Then:

| Harness | First run | Outer loop | Slow loop |
|---|---|---|---|
| Claude Code | `claude` → "use the run-issue skill on issues/001-complete-item.md" | `./loop.sh issues` | `./loop.sh gardener` (cron it nightly) |
| Codex | `codex`, run `/hooks`, trust the three hooks, then "use the run-issue skill on issues/001-complete-item.md" | `./loop.sh issues` | `./loop.sh gardener` |
| Kiro Crew | open a chat in the folder: "run issue issues/001-complete-item.md" | a cron that sweeps `issues/` against `runs.log` | `cron_add` with the gardener message in the steering file |

## What stays as code, on every harness

| Code | Why it cannot be markdown |
|---|---|
| `scripts/verify.sh` | the model must not decide whether tests passed |
| `scripts/post_edit_gate.sh`, `scripts/stop_gate.sh` | the verify→fix edge and "not done while red" enforced by the harness, so no prompt can talk around them |
| `scripts/validate_proposal.py` | the gate on agents building agents: parses every proposed agent file, refuses write or shell tools on a new agent, checks `build < verify < review < ship` still holds in the skill, replays the issues |

Everything else (agent prompts, the graph, the lessons, the gardener's judgment) is markdown.

## Where the fresh-context reviewer comes from

| Harness | Mechanism |
|---|---|
| Claude Code | every subagent starts with its own context window; the skill tells the main thread to pass only issue + diff |
| Codex | a spawned custom agent starts a new thread; it inherits the sandbox, so read-only is by instruction, backed by hooks and the validator |
| Kiro Crew | `spawn_run(agent="todo-reviewer", include_memory=false, include_lessons=false)` |

## Honest gaps

- Hook matcher strings for Codex (`apply_patch`) and Kiro CLI (`postToolUse` / `fs_write`) were taken from the current docs and agent files, not executed here (TO BE CONFIRMED on your machine with `/hooks` and `kiro-cli agent validate`).
- `install.sh` ran clean for all three in a scratch clone. The hooks were exercised directly (exit 2 on red, 0 on green, 0 on non-app edits). No live model run was made from this sandbox.
- The gardener on these ports proposes in prose and writes agent files, so its judgment is a model's. `validate_proposal.py` is what keeps that safe, not the prompt.
