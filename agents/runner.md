---
name: runner
description: Runs the test suite and follows the exit code. Not a model. Serves the verify and ship nodes.
tools: run_tests
kind: script
command: python3 -m unittest -q
---

The runner is the hard edge of the graph. It executes the command above inside `app/` and reports pass or fail from the exit code. No prompt, no judgment, nothing a model can argue with.
