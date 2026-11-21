#!/usr/bin/env bash
# PostToolUse hook on file edits: run the tests right after every write to app/ and
# hand the failure straight back to the model (exit 2 = show stderr to the model).
# This is the verify -> fix edge enforced by the harness instead of by prose.
payload="$(cat)"
case "$payload" in
  *"app/todo.py"*|*"app/test_todo.py"*) ;;
  *) exit 0 ;;
esac
out="$("$(dirname "$0")/verify.sh")"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "verify: tests red after your edit. Fix before anything else." >&2
  echo "$out" | tail -20 >&2
  exit 2
fi
exit 0
