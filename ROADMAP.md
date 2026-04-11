# Roadmap

## Phase 1.0: Jules Automation Integration
**Goal**: Wire up the Jules API for autonomous PR processing and configure its internal scheduled tasks for recurring codebase sweeps.
**Status**: Completed

- [x] Update `AGENTS.md` to define test/debug/validate workflows natively for Jules.
- [x] Configure GitHub webhooks to trigger Jules API on PR creation.
- [x] Setup scheduled auditing tasks within Jules UI.

## Phase 1.1: Close Milestone 1.0 Documentation Gaps
**Goal**: Retroactively generate missing canonical plans, summaries, and verifications mandated by the GSD workflow.
**Status**: Completed

- [x] Create `REQUIREMENTS.md`
- [x] Create Phase 1.0 `VERIFICATION.md`
- [x] Create Phase 1.0 `SUMMARY.md`

## Phase 2.0: Zapier Workflow Replacement Expansion (Triggers & Notifications)
**Goal**: Expand the native Cloudflare Worker proxy to handle a variety of GitHub events, dispatch notifications to external channels like Discord/Slack, and deploy to production.
**Status**: Completed

- [x] Add event listeners for Issues, PR Merges, and Discussions in `proxy/src/index.ts`.
- [x] Implement outbound Webhook dispatch for Discord/Slack notifications.
- [x] Configure `wrangler` secrets and deploy the worker to production.
