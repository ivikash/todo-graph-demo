#!/usr/bin/env python3
"""Generate each harness's agent files from the one source of truth, agents/*.md.

    python3 ports/gen_agents.py claude-code <out-dir>   # .claude/agents/<name>.md
    python3 ports/gen_agents.py codex       <out-dir>   # .codex/agents/<name>.toml
    python3 ports/gen_agents.py kiro-crew   <out-dir>   # .kiro/agents/todo-<name>.json

The abstract tool names in agents/*.md (read, write, run_tests) map to each harness's real
tool names below. Script agents (kind: script, the runner) are not emitted: the harness runs
them through hooks and the run-issue skill, not as a model.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agents import load  # noqa: E402

TOOLS = {
    "claude-code": {"read": ["Read", "Grep", "Glob"], "write": ["Edit", "Write"]},
    "codex": {},  # Codex agents inherit the parent's sandbox; read-only is by instruction
    "kiro-crew": {"read": ["fs_read", "grep", "glob"], "write": ["fs_write"]},
}
MODELS = {
    "claude-code": {"default": "sonnet", "reviewer": "opus", "scribe": "haiku"},
    "codex": {"default": "gpt-6.2-sol", "planner": "gpt-6-luna", "scribe": "gpt-6-luna"},
}


def tools_for(harness, agent):
    out = []
    for t in agent["tools"]:
        for real in TOOLS[harness].get(t, []):
            if real not in out:
                out.append(real)
    return out


def model_for(harness, agent):
    m = MODELS.get(harness, {})
    return m.get(agent["name"], m.get("default", "default")) if agent.get("model", "default") == "default" else agent["model"]


def claude(agent, out):
    tools = ", ".join(tools_for("claude-code", agent))
    (out / f"{agent['name']}.md").write_text(
        f"---\nname: {agent['name']}\ndescription: {agent['description']}\ntools: {tools}\nmodel: {model_for('claude-code', agent)}\n---\n\n{agent['body']}\n")


def codex(agent, out):
    effort = "high" if agent["name"] in ("reviewer", "planner") else "medium"
    body = agent["body"].replace('"""', "'''")
    (out / f"{agent['name']}.toml").write_text(
        f'# generated from agents/{agent["name"]}.md by ports/gen_agents.py\n'
        f'name = "{agent["name"]}"\n'
        f'description = "{agent["description"]}"\n'
        f'model = "{model_for("codex", agent)}"\n'
        f'model_reasoning_effort = "{effort}"\n'
        f'developer_instructions = """\n{body}\n"""\n')


def kiro(agent, out):
    tools = tools_for("kiro-crew", agent)
    spec = {
        "name": f"todo-{agent['name']}",
        "description": agent["description"],
        "prompt": agent["body"].replace("`", ""),
        "tools": tools,
        "allowedTools": [t for t in tools if t != "fs_write"],
        "resources": ["file://lessons.md", "file://issues/*.md", "file://app/*.py"],
    }
    if "write" in agent["tools"]:
        spec["hooks"] = {"postToolUse": [{"matcher": "fs_write", "command": "bash scripts/post_edit_gate.sh"}]}
    (out / f"todo-{agent['name']}.json").write_text(json.dumps(spec, indent=2) + "\n")


EMIT = {"claude-code": claude, "codex": codex, "kiro-crew": kiro}


def main(harness, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for agent in load(ROOT / "agents").values():
        if agent["kind"] != "model":
            continue
        EMIT[harness](agent, out)
        n += 1
    print(f"{harness}: wrote {n} agent files to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in EMIT:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
