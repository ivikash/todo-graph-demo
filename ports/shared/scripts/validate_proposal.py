#!/usr/bin/env python3
"""Validate a gardener proposal for the markdown-native ports.

    python3 scripts/validate_proposal.py proposals/<ts>

Checks (all deterministic, none ask a model):
  agents    every agent file in the proposal parses, and no new agent carries a write or shell tool
  graph     the run-issue skill still has verify before review and review before ship
  replay    if the proposal carries a graph.json, reuse gardener.py's replay; otherwise report
            that replay needs a scratch run of the issues through the proposed skill
Writes VALIDATED or REJECTED into the proposal folder and appends the table to report.md.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

def _root():
    """The repo root is the nearest ancestor holding app/ and issues/ (script may live in scripts/ or ports/shared/scripts/)."""
    for p in Path(__file__).resolve().parents:
        if (p / "app").is_dir() and (p / "issues").is_dir():
            return p
    raise SystemExit("cannot find repo root (a directory with app/ and issues/)")


ROOT = _root()
WRITE_TOOLS = {"write", "run_tests", "deploy", "shell",                       # agents/*.md abstract names
               "Edit", "Write", "MultiEdit", "Bash", "NotebookEdit",          # Claude Code
               "apply_patch", "shell", "local_shell",                         # Codex
               "fs_write", "execute_bash", "code"}                            # Kiro


def agent_tools(path: Path):
    text = path.read_text()
    if path.suffix == ".json":
        return set(json.loads(text).get("tools", []))
    if path.suffix == ".toml":
        m = re.search(r"^tools\s*=\s*\[(.*?)\]", text, re.S | re.M)
        return set(t.strip().strip('"') for t in m.group(1).split(",") if t.strip()) if m else set()
    m = re.search(r"^tools:\s*(.+)$", text, re.M)                              # Claude .md frontmatter
    return set(t.strip() for t in m.group(1).split(",")) if m else set()


def check_agents(pdir: Path):
    errs, seen = [], 0
    for f in list(pdir.rglob("agents/*")):
        if f.suffix not in (".md", ".toml", ".json"):
            continue
        seen += 1
        try:
            tools = agent_tools(f)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{f.name}: unparsable ({e})")
            continue
        bad = tools & WRITE_TOOLS
        if bad:
            errs.append(f"{f.name}: new agent asks for write/shell tools {sorted(bad)}")
    return errs, f"{seen} agent file(s) checked"


def check_graph_order(pdir: Path):
    skill = next(iter(pdir.rglob("run-issue/SKILL.md")), None) or ROOT / "ports/shared/skills/run-issue/SKILL.md"
    text = skill.read_text()
    pos = {k: text.find(f"**{k}**") for k in ("build", "verify", "review", "ship")}
    if any(v < 0 for v in pos.values()):
        return ["run-issue skill lost a required node"], str(skill)
    if not (pos["build"] < pos["verify"] < pos["review"] < pos["ship"]):
        return ["node order changed: must be build < verify < review < ship"], str(skill)
    return [], f"build < verify < review < ship in {skill.relative_to(ROOT)}"


def check_replay(pdir: Path):
    if (pdir / "graph.json").exists():
        p = subprocess.run([sys.executable, str(ROOT / "gardener.py"), "validate", str(pdir)], capture_output=True, text=True)
        line = next((l for l in p.stdout.splitlines() if l.startswith("| replay")), "")
        return ([] if "PASS" in line else ["replay regressed or failed"]), line.strip("| ").replace(" | ", ": ", 1)
    return [], "no graph.json: replay the issues through the proposed skill in a scratch clone and compare runs.log (manual)"


def main(pdir):
    pdir = Path(pdir)
    rows = []
    for name, fn in (("agents", check_agents), ("graph order", check_graph_order), ("replay", check_replay)):
        errs, detail = fn(pdir)
        rows.append((name, not errs, "; ".join(errs) or detail))
    ok = all(r[1] for r in rows)
    table = ["| Check | Result | Detail |", "|---|---|---|"] + [f"| {n} | {'PASS' if v else 'FAIL'} | {d} |" for n, v, d in rows]
    verdict = "VALIDATED: safe to apply (human step)" if ok else "REJECTED"
    print("\n".join(table + ["", verdict]))
    with open(pdir / "report.md", "a") as fh:
        fh.write("\n## Validation\n\n" + "\n".join(table) + f"\n\n{verdict}\n")
    (pdir / ("VALIDATED" if ok else "REJECTED")).touch()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
