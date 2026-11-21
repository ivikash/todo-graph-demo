#!/usr/bin/env bash
# The hard edge. Exit 0 = green, anything else = red. Prints the test output.
# Used by: the run-issue skill (step 3 and 6), every harness's PostToolUse and Stop hooks.
set -u
# repo root = nearest ancestor with app/ (script may live in scripts/ or ports/shared/scripts/)
ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ ! -d "$ROOT/app" ] && [ "$ROOT" != "/" ]; do ROOT="$(dirname "$ROOT")"; done
cd "$ROOT/app" || exit 2
python3 -m unittest -q 2>&1
exit "${PIPESTATUS[0]}"
