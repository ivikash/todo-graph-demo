#!/usr/bin/env bash
# The outer loop Boris talks about: nobody prompts; this script does.
#   ./loop.sh issues          run every open issue through the graph, headless
#   ./loop.sh gardener        run the slow loop once (put this in cron, nightly)
# Run from a checkout prepared by ports/install.sh claude-code.
set -euo pipefail
cd "$(dirname "$0")/../.."
case "${1:-issues}" in
  issues)
    for issue in issues/*.md; do
      echo "== $issue"
      claude -p "Use the run-issue skill on $issue." \
        --allowedTools "Task,Read,Grep,Glob,Edit,Write,Bash(bash scripts/*),Bash(git *),Bash(python3 *)" \
        --output-format text
    done ;;
  gardener)
    claude -p "Use the gardener skill. Propose at most one change, validate it, do not apply." \
      --allowedTools "Read,Grep,Glob,Write,Bash(python3 scripts/*)" --output-format text ;;
  *) echo "usage: loop.sh issues|gardener"; exit 2 ;;
esac
