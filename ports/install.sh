#!/usr/bin/env bash
# Wire one harness into THIS checkout. Run from the repo root in your own terminal:
#   bash ports/install.sh claude-code | codex | kiro-crew
# Copies the shared skills and scripts into place and the harness-specific files to
# the paths that harness reads. Nothing outside this checkout is touched except
# where noted for Kiro Crew.
set -euo pipefail
cd "$(dirname "$0")/.."
H="${1:-}"
[ -n "$H" ] || { echo "usage: bash ports/install.sh claude-code|codex|kiro-crew"; exit 2; }

mkdir -p scripts
cp ports/shared/scripts/*.sh ports/shared/scripts/*.py scripts/ && chmod +x scripts/*.sh scripts/*.py
touch runs.log
[ -f lessons.md ] || cp ports/shared/lessons.template.md lessons.md

case "$H" in
  claude-code)
    mkdir -p .claude/agents .claude/skills
    cp ports/claude-code/.claude/agents/*.md .claude/agents/
    cp -r ports/shared/skills/run-issue ports/shared/skills/gardener .claude/skills/
    cp ports/claude-code/claude-settings.template.json .claude/settings.json
    cp ports/claude-code/CLAUDE.md CLAUDE.md
    cp ports/claude-code/loop.sh loop.sh && chmod +x loop.sh
    echo "Claude Code wired. Try:  claude  then  'use the run-issue skill on issues/001-complete-item.md'   or   ./loop.sh issues" ;;
  codex)
    mkdir -p .codex/agents .codex/skills
    cp ports/codex/agents/*.toml .codex/agents/
    cp -r ports/shared/skills/run-issue ports/shared/skills/gardener .codex/skills/
    cp ports/codex/codex-hooks.template.json .codex/hooks.json
    cp ports/codex/AGENTS.md AGENTS.md
    cp ports/codex/loop.sh loop.sh && chmod +x loop.sh
    echo "Codex wired. Start 'codex' once, run /hooks and trust the three hooks, then ./loop.sh issues" ;;
  kiro-crew)
    mkdir -p .kiro/agents .kiro/steering
    cp ports/kiro-crew/agents/*.json .kiro/agents/
    cp ports/kiro-crew/steering/todo-graph.md .kiro/steering/
    SK="${KIROCREW_HOME:-$HOME/.kiro/crew}/skills"
    mkdir -p "$SK"
    ln -sfn "$PWD/ports/shared/skills/run-issue" "$SK/todo-run-issue"
    ln -sfn "$PWD/ports/shared/skills/gardener" "$SK/todo-gardener"
    for a in .kiro/agents/*.json; do kiro-cli agent validate --path "$a" >/dev/null 2>&1 && echo "valid: $a" || echo "check: $a (kiro-cli agent validate)"; done
    echo "Kiro Crew wired. Open a chat in this folder and say: 'run issue issues/001-complete-item.md'. Skills linked as $SK/todo-run-issue and todo-gardener." ;;
  *) echo "unknown harness: $H"; exit 2 ;;
esac
