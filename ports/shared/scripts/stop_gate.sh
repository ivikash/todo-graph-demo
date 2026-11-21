#!/usr/bin/env bash
# Stop hook for Claude Code and Codex: refuse to end the turn while tests are red.
# Both harnesses read exit 2 as "block, and show stderr to the model".
# Reads the hook payload on stdin (unused here, kept for the contract).
cat >/dev/null
out="$("$(dirname "$0")/verify.sh")"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "Tests are red. You may not stop. Fix the root cause, do not weaken tests. Output:" >&2
  echo "$out" | tail -20 >&2
  exit 2
fi
exit 0
