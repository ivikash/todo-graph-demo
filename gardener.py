#!/usr/bin/env python3
"""The slow loop: read what the runs taught us, propose ONE change to the graph itself,
validate it, and leave it as a draft for a human to apply.

    python3 gardener.py propose            # reads runs/ + lessons.md, writes proposals/<ts>/
    python3 gardener.py validate <dir>     # schema, least privilege, replay vs baseline
    python3 gardener.py apply <dir>        # the human step: copy the proposed graph live

The gardener never edits the product (app/). It edits the structure that edits the product.
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROPOSALS = ROOT / "proposals"
sys.path.insert(0, str(ROOT))
from agents import load as load_agents  # noqa: E402

AGENT_TEMPLATE = """---
name: {name}
description: {description}
tools: {tools}
model: default
---

{body}
"""

# What a repeated lesson tag turns into. "prose" = patch a prompt. "node" = a new agent + node,
# i.e. the graph grows a new worker; that is the "agents build agents" step.
CATALOG = {
    "untested-acceptance-line": {
        "kind": "node",
        "agent": {"name": "spec-checker", "tools": ["read"], "purpose": "map every acceptance line to a named test before any code is written",
                  "body": "You are the spec-checker. You read, you never edit. Given an issue and a plan, output a checklist with one line per acceptance item in the form `- <acceptance line> -> test_<name>`. Include error paths and copy/aliasing semantics. Output only the checklist."},
        "node": {"name": "spec-check", "after": "plan", "before": "build"},
        "prompt": (
            "You are the spec-check node. Read only.\n\nIssue:\n{{issue}}\n\nPlan:\n{{plan}}\n\n"
            "Output a checklist with one line per acceptance item in the form `- <acceptance line> -> test_<name>`. "
            "Include error paths and copy/aliasing semantics. Output only the checklist."
        ),
    },
    "missing-error-path": {
        "kind": "prose",
        "prompt_file": "build.md",
        "append": "\nBefore writing code, list every acceptance line that names an exception and write that test first.\n",
    },
}


def load_runs(runs_dir):
    return [json.loads(p.read_text()) for p in sorted(Path(runs_dir).glob("*.json"))]


def lesson_tags(lessons_path):
    tags = []
    for line in Path(lessons_path).read_text().splitlines():
        if line.startswith("|") and "|---" not in line and "| Date |" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                tags.append(cells[1])
    return tags


def propose(graph_path=ROOT / "graph.json", runs_dir=ROOT / "runs", lessons=ROOT / "lessons.md", threshold=1):
    runs = [r for r in load_runs(runs_dir) if "proposals" not in r["graph"]]
    tags = Counter(lesson_tags(lessons))
    total_loops = sum(r["loops"] for r in runs)
    if not runs or total_loops == 0 or not tags:
        print("nothing to improve: no runs needed a fix loop")
        return None
    # Most frequent tag wins. On a tie prefer the structural fix (a node) over a prompt rule,
    # because a rule in prose is the thing agents drift away from; a node cannot be skipped.
    ranked = sorted(tags.items(), key=lambda kv: (kv[1], CATALOG.get(kv[0], {}).get("kind") == "node"), reverse=True)
    tag, n = ranked[0]
    if n < threshold or tag not in CATALOG:
        print(f"most frequent lesson '{tag}' x{n}: below threshold or no catalog entry; leaving it as prose")
        return None

    graph = json.loads(Path(graph_path).read_text())
    entry = CATALOG[tag]
    out = PROPOSALS / dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out.mkdir(parents=True)
    report = [f"# Proposal from gardener ({out.name})", "",
              f"Evidence: {len(runs)} runs, {total_loops} fix loops total, most frequent lesson tag `{tag}` x{n}.", ""]

    if entry["kind"] == "node":
        ag, nd = entry["agent"], entry["node"]
        (out / "agents").mkdir()
        (out / "agents" / f"{ag['name']}.md").write_text(AGENT_TEMPLATE.format(
            name=ag["name"], description=ag["purpose"][0].upper() + ag["purpose"][1:] + ".", tools=", ".join(ag["tools"]), body=ag["body"]))
        graph["nodes"][nd["after"]]["next"] = nd["name"]
        graph["nodes"][nd["name"]] = {"agent": ag["name"], "next": nd["before"]}
        (out / "prompts").mkdir()
        (out / "prompts" / f"{nd['name']}.md").write_text(entry["prompt"])
        report += [f"Change: new agent `{ag['name']}` (tools {ag['tools']}, file agents/{ag['name']}.md) and new node `{nd['name']}` between `{nd['after']}` and `{nd['before']}`.",
                   f"Why: {ag['purpose']}."]
    else:
        (out / "prompts").mkdir()
        src = (ROOT / "prompts" / entry["prompt_file"]).read_text()
        (out / "prompts" / entry["prompt_file"]).write_text(src + entry["append"])
        report += [f"Change: append a rule to prompts/{entry['prompt_file']}.", f"Rule: {entry['append'].strip()}"]

    (out / "graph.json").write_text(json.dumps(graph, indent=2))
    (out / "report.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nproposal written to {out.relative_to(ROOT)}  (not live; run validate, then apply)")
    return out


def agents_for(pdir):
    """Base agents plus the proposal's own agent files layered on top."""
    agents = load_agents(ROOT / "agents")
    if (pdir / "agents").is_dir():
        agents.update(load_agents(pdir / "agents"))
    return agents


def check_schema(graph, agents):
    errs = []
    nodes = graph["nodes"]
    if graph["start"] not in nodes:
        errs.append("start node missing")
    for name, spec in nodes.items():
        if spec["agent"] not in agents:
            errs.append(f"{name}: unknown agent {spec['agent']} (no agents/<name>.md)")
        for k in ("next", "pass", "fail"):
            tgt = spec.get(k)
            if tgt is not None and tgt not in nodes:
                errs.append(f"{name}.{k} -> {tgt} does not exist")
    seen, stack = set(), [graph["start"]]
    while stack:
        n = stack.pop()
        if n in seen or n is None:
            continue
        seen.add(n)
        stack += [nodes[n].get(k) for k in ("next", "pass", "fail")]
    for n in set(nodes) - seen:
        errs.append(f"{n} unreachable from start")
    return errs


def check_privilege(base, prop):
    """base and prop are agent dicts (name -> parsed agent file)."""
    errs = []
    allowed = set(t for a in base.values() for t in a["tools"])
    for name, a in prop.items():
        if name in base:
            if set(a["tools"]) - set(base[name]["tools"]):
                errs.append(f"agent {name} gained tools {set(a['tools']) - set(base[name]['tools'])}")
        else:
            if set(a["tools"]) - allowed:
                errs.append(f"new agent {name} asks for tools nobody has: {set(a['tools']) - allowed}")
            if "write" in a["tools"]:
                errs.append(f"new agent {name} asks for write; a proposal may add read-only workers only")
    return errs


def replay(graph_path, prompts_dir, label, extra_agents=None):
    """Run every issue through a graph against a fresh copy of app/, fake mode. Returns loops, failures."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        shutil.copytree(ROOT / "app", td / "app")
        shutil.copytree(ROOT / "prompts", td / "prompts")
        if prompts_dir and Path(prompts_dir).exists():
            for p in Path(prompts_dir).glob("*.md"):
                shutil.copy(p, td / "prompts" / p.name)
        (td / "lessons.md").write_text((ROOT / "lessons.md").read_text().split("|---|")[0] + "|---|---|---|---|\n")
        loops = fails = 0
        green = True
        for issue in sorted((ROOT / "issues").glob("*.md")):
            p = subprocess.run([sys.executable, str(ROOT / "run.py"), str(issue), "--fake", "--quiet",
                                "--graph", str(graph_path), "--app", str(td / "app"), "--runs", str(td / "runs"),
                                "--lessons", str(td / "lessons.md"), "--prompts", str(td / "prompts")]
                               + (["--extra-agents", str(extra_agents)] if extra_agents else []),
                               capture_output=True, text=True)
            green &= p.returncode == 0
        for r in load_runs(td / "runs"):
            loops += r["loops"]
            fails += len(r["failures"])
        print(f"  replay {label:8s}: fix loops={loops} failures={fails} all tests green={green}")
        return loops, fails, green


def validate(proposal_dir):
    pdir = Path(proposal_dir)
    prop = json.loads((pdir / "graph.json").read_text())
    base_agents, prop_agents = load_agents(ROOT / "agents"), agents_for(pdir)
    verdicts = []
    s = check_schema(prop, prop_agents)
    verdicts.append(("schema", not s, "; ".join(s) or "start reachable, every edge resolves, every node reachable"))
    p = check_privilege(base_agents, prop_agents)
    verdicts.append(("least privilege", not p, "; ".join(p) or "no agent gained tools, new agents read-only"))
    print("replaying all issues in fake mode, baseline then proposal:")
    b = replay(ROOT / "graph.json", None, "baseline")
    n = replay(pdir / "graph.json", pdir / "prompts", "proposal", extra_agents=pdir / "agents")
    better = n[2] and n[0] <= b[0] and n[1] <= b[1]
    verdicts.append(("replay", better, f"baseline loops={b[0]} failures={b[1]}; proposal loops={n[0]} failures={n[1]}"))
    ok = all(v[1] for v in verdicts)
    lines = ["", "| Check | Result | Detail |", "|---|---|---|"] + [f"| {k} | {'PASS' if v else 'FAIL'} | {d} |" for k, v, d in verdicts]
    lines.append("")
    lines.append("VALIDATED: safe to apply (human step)" if ok else "REJECTED: proposal discarded")
    print("\n".join(lines))
    with open(pdir / "report.md", "a") as fh:
        fh.write("\n## Validation\n" + "\n".join(lines) + "\n")
    (pdir / ("VALIDATED" if ok else "REJECTED")).touch()
    return ok


def apply(proposal_dir):
    pdir = Path(proposal_dir)
    if not (pdir / "VALIDATED").exists():
        print("refusing: proposal is not VALIDATED")
        return 1
    shutil.copy(ROOT / "graph.json", pdir / "graph.before.json")
    shutil.copy(pdir / "graph.json", ROOT / "graph.json")
    for p in (pdir / "prompts").glob("*.md"):
        shutil.copy(p, ROOT / "prompts" / p.name)
    for p in (pdir / "agents").glob("*.md") if (pdir / "agents").is_dir() else []:
        shutil.copy(p, ROOT / "agents" / p.name)
    (pdir / "APPLIED").touch()
    print(f"applied {pdir.name}: graph.json, prompts and agents updated (previous graph kept at {pdir.name}/graph.before.json)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "propose"
    if cmd == "propose":
        sys.exit(0 if propose() else 1)
    if cmd == "validate":
        sys.exit(0 if validate(sys.argv[2]) else 1)
    if cmd == "apply":
        sys.exit(apply(sys.argv[2]))
    print(__doc__)
