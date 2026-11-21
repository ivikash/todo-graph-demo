#!/usr/bin/env bash
# The outer loop for Codex. codex exec is non-interactive: it works in the sandbox,
# streams progress to stderr and prints only the final message to stdout.
#   ./loop.sh issues          run every issue through the graph
#   ./loop.sh gardener        run the slow loop once (cron it nightly)
# Hooks must be trusted once via /hooks in an interactive session; or add
# --dangerously-bypass-hook-trust here if you vet hooks outside Codex.
set -euo pipefail
cd "$(dirname "$0")/../.."
case "${1:-issues}" in
  issues)
    for issue in issues/*.md; do
      echo "== $issue"
      codex exec --full-auto "Use the run-issue skill on $issue. Delegate each node to the named custom agent and wait for it."
    done ;;
  gardener)
    codex exec --full-auto "Use the gardener skill. Propose at most one change, validate it with scripts/validate_proposal.py, do not apply." ;;
  *) echo "usage: loop.sh issues|gardener"; exit 2 ;;
esac
