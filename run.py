#!/usr/bin/env python3
"""Walk graph.json over one issue.

Every node is one fresh agent call (a new `kiro-cli chat --no-interactive` process, so no
node remembers another's context) or, for the runner agent, a plain test run. Edges carry
pass/fail. The `fix` node loops back to `verify` until green or max_loops.

    python3 run.py issues/001-complete-item.md            # real agents via kiro-cli
    python3 run.py issues/001-complete-item.md --fake     # deterministic stand-ins, no tokens
    python3 run.py ... --graph proposals/<ts>/graph.json  # try a proposed graph

Each run writes runs/<timestamp>-<issue>.json (nodes visited, loops, verdicts, durations)
and, when the run needed a fix, one row to lessons.md.
"""
import argparse
import datetime as dt
import difflib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from agents import load as load_agents, strip_frontmatter  # noqa: E402


def read(p):
    return Path(p).read_text()


def lessons_rows(path):
    rows = [l for l in read(path).splitlines() if l.startswith("|") and not l.startswith("|---") and "| Date |" not in l]
    return "\n".join(rows) if rows else "(none yet)"


def render(prompts_dir, name, **kw):
    text = strip_frontmatter(read(prompts_dir / f"{name}.md"))
    for k, v in kw.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def run_tests(app):
    p = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=app, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def snapshot(app):
    return {f.name: f.read_text() for f in app.glob("*.py")}


def diff_since(app, before):
    out = []
    for name, old in before.items():
        new = (app / name).read_text()
        out += difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{name}", f"b/{name}", lineterm="")
    return "\n".join(out) or "(no changes)"


def real_llm(agent_def, prompt, cwd, timeout=600):
    """One fresh process per node. The agent file's body is its standing instruction, the node prompt follows."""
    cmd = ["kiro-cli", "chat", "--no-interactive"]
    if "write" in agent_def["tools"]:
        cmd.append("--trust-all-tools")
    cmd.append(agent_def["body"] + "\n\n" + prompt)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout + p.stderr).strip()
    if p.returncode != 0 or "Not logged in" in out or not out:
        raise RuntimeError(f"agent call failed (exit {p.returncode}): {out[-300:] or '(no output)'}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--graph", default=ROOT / "graph.json")
    ap.add_argument("--app", default=ROOT / "app")
    ap.add_argument("--runs", default=ROOT / "runs")
    ap.add_argument("--lessons", default=ROOT / "lessons.md")
    ap.add_argument("--prompts", default=ROOT / "prompts")
    ap.add_argument("--agents", default=ROOT / "agents", help="directory of agent markdown files")
    ap.add_argument("--extra-agents", default=None, help="a second agents dir layered on top (a proposal's)")
    ap.add_argument("--fake", action="store_true", help="deterministic stand-ins, no LLM calls")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    graph = json.loads(read(a.graph))
    agents = load_agents(a.agents)
    if a.extra_agents and Path(a.extra_agents).is_dir():
        agents.update(load_agents(a.extra_agents))
    missing = {spec["agent"] for spec in graph["nodes"].values()} - set(agents)
    if missing:
        sys.exit(f"graph names agents with no file in {a.agents}: {sorted(missing)}")
    app, runs_dir, prompts = Path(a.app), Path(a.runs), Path(a.prompts)
    runs_dir.mkdir(exist_ok=True)
    issue_text = read(a.issue)
    issue_id = re.match(r"(\d+)", Path(a.issue).name).group(1)
    today = dt.date.today().isoformat()

    state = {"issue_id": issue_id, "issue": issue_text, "plan": "", "failures": [], "loops": 0, "date": today}
    before = snapshot(app)
    trace = []
    log = (lambda *x: None) if a.quiet else (lambda *x: print(*x, flush=True))

    if a.fake:
        from fake_world import fake_llm
        llm = lambda node, agent, prompt: fake_llm(node, agent, state, app)
    else:
        llm = lambda node, agent, prompt: real_llm(agents[agent], prompt, app)

    node = graph["start"]
    while node:
        spec = graph["nodes"][node]
        agent = spec["agent"]
        t0 = time.time()
        log(f"\n== {node} ({agent})")
        nxt, note = spec.get("next"), ""

        if agents[agent]["kind"] == "script":
            ok, out = run_tests(app)
            note = out.splitlines()[-1] if out else ""
            if node == "verify":
                if ok:
                    nxt = spec["pass"]
                else:
                    state["failures"].append({"node": node, "kind": "tests", "detail": out[-1500:]})
                    nxt = spec["fail"]
            log(("PASS " if ok else "FAIL ") + note)
        else:
            lessons = lessons_rows(a.lessons)
            if node == "plan":
                prompt = render(prompts, "plan", issue=issue_text, lessons=lessons)
            elif node == "build":
                prompt = render(prompts, "build", issue=issue_text, plan=state["plan"], lessons=lessons)
            elif node == "fix":
                prompt = render(prompts, "fix", issue=issue_text, lessons=lessons, failure=state["failures"][-1]["detail"])
            elif node == "review":
                prompt = render(prompts, "review", issue=issue_text, diff=diff_since(app, before))
            elif node == "learn":
                fails = "\n".join(f"- {f['node']}/{f['kind']}: {f['detail'].splitlines()[-1][:160]}" for f in state["failures"]) or "(none)"
                prompt = render(prompts, "learn", issue_title=issue_text.splitlines()[0], loops=state["loops"], failures=fails)
            else:  # a node the gardener added; its prompt file is named after the node
                prompt = render(prompts, node, issue=issue_text, plan=state["plan"], lessons=lessons)
            if node == "fix" and state["loops"] >= spec.get("max_loops", 3):
                log(f"max_loops={spec.get('max_loops', 3)} reached, stopping with tests red")
                trace.append({"node": node, "agent": agent, "secs": 0, "note": "max_loops", "next": None})
                break
            try:
                out = llm(node, agent, prompt)
            except RuntimeError as e:  # an agent that cannot run is a stop, not a retry
                log(f"ABORT: {e}")
                state["failures"].append({"node": node, "kind": "agent_error", "detail": str(e)})
                trace.append({"node": node, "agent": agent, "secs": round(time.time() - t0, 2), "note": str(e)[:200], "next": None})
                break
            note = out.strip().splitlines()[-1][:200] if out.strip() else ""
            log(note)

            if node == "plan":
                state["plan"] = out
            elif node == "fix":
                state["loops"] += 1
            elif node == "review":
                m = re.search(r"VERDICT:\s*(PASS|FAIL)(.*)", out)
                if m and m.group(1) == "PASS":
                    nxt = spec["pass"]
                else:
                    state["failures"].append({"node": node, "kind": "review", "detail": (m.group(2).strip() if m else out[-800:])})
                    nxt = spec["fail"]
            elif node == "learn":
                row = out.strip().splitlines()[-1] if out.strip() else ""
                if row.startswith("|") and "NO LESSON" not in out:
                    with open(a.lessons, "a") as fh:
                        fh.write(row + "\n")
                    log("lesson recorded")

        trace.append({"node": node, "agent": agent, "secs": round(time.time() - t0, 2), "note": note, "next": nxt})
        node = nxt

    ok, _ = run_tests(app)
    record = {
        "issue": Path(a.issue).name, "graph": str(a.graph), "fake": a.fake, "date": today,
        "loops": state["loops"], "failures": state["failures"], "tests_green": ok, "trace": trace,
    }
    out_path = runs_dir / f"{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{issue_id}.json"
    out_path.write_text(json.dumps(record, indent=2))
    log(f"\nrun: loops={state['loops']} failures={len(state['failures'])} tests_green={ok} -> {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
