"""Agent definitions are markdown files in agents/ with a frontmatter header and a body.

    ---
    name: coder
    description: one line
    tools: read, write          # abstract names: read, write, run_tests
    model: default
    kind: script                # optional, a non-model agent (the runner)
    command: python3 -m unittest -q
    fresh_context: true         # optional
    ---
    <body: the agent's standing instructions>

The same file is the single source of truth for run.py, gardener.py, validate_proposal.py and
the per-harness files that ports/gen_agents.py generates (Claude Code .md, Codex .toml, Kiro .json).
"""
from pathlib import Path


def parse(path):
    text = Path(path).read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing frontmatter")
    meta, i = {}, 1
    while i < len(lines) and lines[i].strip() != "---":
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip()
        i += 1
    body = "\n".join(lines[i + 1:]).strip()
    for k in ("name", "description", "tools"):
        if k not in meta:
            raise ValueError(f"{path}: frontmatter needs '{k}'")
    meta["tools"] = [t.strip() for t in meta["tools"].split(",") if t.strip()]
    meta["kind"] = meta.get("kind", "model")
    meta["fresh_context"] = meta.get("fresh_context", "false").lower() == "true"
    meta["body"] = body
    meta["path"] = str(path)
    return meta


def load(agents_dir):
    agents = {}
    for p in sorted(Path(agents_dir).glob("*.md")):
        a = parse(p)
        agents[a["name"]] = a
    return agents


def strip_frontmatter(text):
    """prompts/*.md carry a header too (name, agent, inputs); the runner wants only the template."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:]).lstrip("\n")
    return text
