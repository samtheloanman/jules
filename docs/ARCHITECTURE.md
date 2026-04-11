# Architecture

## System Diagram
The Jules automation system is comprised of two core functional layers:

1. **The Edge Network (Cloudflare Webhook Proxy)**
2. **The Local Scripts (Python Utilities)**

### The Webhook Pipeline
When a developer pushes code to GitHub and opens a Pull Request:
1. **GitHub** natively detects the PR configuration (mapped in `.github/workflows/jules-labels.yml`) and potentially auto-labels it (`jules:test` / `jules:doc`).
2. **GitHub Webhooks** dispatch the event payload to an exposed Cloudflare worker.
3. The **Worker (`proxy/src/index.ts`)** confirms that the action is purely a `pull_request` (opened/synchronized/reopened) and that it has an active `jules:` label.
4. Using the `GITHUB_TOKEN`, the worker queries the latest Commit Statuses via the GitHub API to ensure that another Jules process is not already pending.
5. A `Pending` check script is created on GitHub, notifying the user.
6. The Worker formats the instruction sets (unit test generation or standard review) and fires the HTTP request to `https://jules.googleapis.com/v1alpha/sessions` using the `JULES_API_KEY`.

### Python Utilities Layer
For more advanced, deeper-context debugging that bypasses the single-PR context constraint, the repository supplies localized scripts (`dispatcher.py`, `jules_helper.py`). These can be used to scan historic JSON session blocks (`cmre_history.json`, `remote_sessions.json`) and run programmatic deep dives or codebase audits outside the Edge hook.
