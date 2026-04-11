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

## GSD (Get Stuff Done) Protocol

All agents working on this project (especially Jules in autonomous mode) MUST adhere to the GSD execution framework:

1.  **State Initialization**: Every session MUST begin by reading `.planning/ROADMAP.md` to understand the current milestone and phase targets.
2.  **Context Loading**: Read the `CONTEXT.md` of the active phase to ingest research and background knowledge.
3.  **Mandatory Planning**: For any task involving structural changes or new features, a `PLAN.md` MUST be created (or followed if already present) before code modifications.
4.  **Proof of Implementation**: Update the relevant phase `SUMMARY.md` with a detailed list of changes made during the turn.
5.  **Verified Completion**: Run automated tests for all logic changes. A task is not complete until a `VERIFICATION.md` file is generated documenting passing tests and manual verification steps.
6.  **Roadmap Sync**: Upon conclusion of a phase, update `ROADMAP.md` by marking the corresponding items as completed (`[x]`).
