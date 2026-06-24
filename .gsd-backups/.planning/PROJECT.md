# Project: Jules

## Overview
Jules is an autonomous AI automation layer that bridges GitHub event triggers (PRs, Issues, Comments) with the Jules AI engine. It enables "Push-to-Review" and "Comment-to-Dispatch" workflows, allowing a single developer to orchestrate a fleet of AI agents (Jules, Claude, Antigravity) natively from GitHub.

## Core Goal
Eliminate manual oversight and task dispatching by using a serverless edge proxy to manage the AI execution cycle.

## Tech Stack
- **Edge**: Cloudflare Workers (TypeScript)
- **AI**: Jules API (v1alpha)
- **Orchestration**: Python toolkit (`dispatcher.py`, `overseer.py`, `auto_dispatch.py`)
- **Integration**: GitHub Webhooks, HMAC Signature Validation, GitHub Actions

## History

### Milestone 1.0: Automation & Webhooks (Archived)
Implemented the core serverless proxy and GSD documentation framework.
- **Phase 1.0**: Core Webhook integration.
- **Phase 1.1**: GSD Gap closure (Requirements, State, Audit).
- **Phase 2.0**: Expansion to Discord/Slack/Telegram and multi-event handling (Issues/Comments).
- **Phase 3.0**: Autonomous Multi-Agent Dispatch (Overseer integration).
- **Phase 4.0**: Slash Command Orchestration (`/ship`, `/review`, etc.).
- **Phase 4.1**: Security Posture & Webhook Authorization Guards.

## Status
- **Current State**: Active / Production Ready
- **Next Up**: Milestone 2.0 Discovery
