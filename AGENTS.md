# Agent Instructions

This repository defines instructions for generic coding agents and specifically Jules regarding conventions, CI tasks, and project rules.

## Jules-Specific Instructions

When Jules parses this repository in response to an automated scheduled task or PR review, it must adhere to these directives:

### 1. Mandatory Audits (Scheduled Sweeps)
If you are operating as part of a recurring "Scheduled Task", your goal is full codebase validation:
- You MUST run `python check_gh_jules.py` to assert GitHub integration state.
- If fixing bugs, verify changes by ensuring tests pass before concluding the session.

### 2. PR Review Mode
If you are invoked to review a PR (e.g., triggered by `jules:review` or `jules:test` labels):
- For `jules:review`: Read the diff and provide actionable, inline feedback pointing out logical errors, potential data leaks, or unoptimized complexity. Do NOT hallucinate dependencies.
- For `jules:test`: Immediately write accompanying tests for all untested classes introduced in the PR, and push the branch. Ensure tests pass before completion.
