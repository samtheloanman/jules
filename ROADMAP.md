# Roadmap

**Milestone 1.0 (Automation & Webhooks) has been archived.** All completed phases (1.0 - 4.1) can be found in `.planning/milestones/v1.0/`.

---

## Milestone 2.0: The Swarm Orchestrator
**Goal**: Elevate Jules from a solo-reviewer to a management proxy that can assign GitHub issues directly to Local Agents (e.g., `frontend-specialist`) via webhook label logic.
**Status**: Active

## Phase 2.1: Overseer Label Dispatch (Proxy Extension)
**Goal**: Allow Jules to parse `@jules /delegate [agent]` and automatically apply repository labels (e.g., `agent:frontend-specialist`) that the local `overseer.py` daemon can pick up during its next pulse.
**Status**: Completed

- [x] Add `/delegate [agent]` command parser to `proxy/src/index.ts`.
- [x] Implement GitHub API call to apply labels dynamically to the issue/PR.
- [x] Deploy Edge Proxy.

## Phase 2.2: Autonomous CI/CD Pipeline & Review Bot
**Goal**: Implicitly intercept generic `pull_request` webhooks regardless of labels/mentions, acting as a background CI/CD agent that automatically reviews, tests, and merges incoming GSD pipeline code without explicit invocation.
**Status**: Completed

- [x] Modify proxy trigger guards to allow `event === 'pull_request'` explicitly.
- [x] Implement `payload.sender` bot-guard loop prevention.
- [x] Inject CI/CD specific LLM context prompt into the API payload.
- [x] Deploy Edge Proxy.
