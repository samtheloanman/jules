# Configuration

The operational parameters for Jules mapping require a handful of rigid variables to function.

## Webhook Endpoint Constraints
The `proxy/wrangler.toml` manages Cloudflare specifics. If you ever update standard paths, ensure `wrangler deploy` respects your new limits.

## Environment Secrets
> **VERIFY**: Ensure you *never* check in your tokens natively. 

Store these securely inside Cloudflare Edge variables or `.dev.vars`:
- `GITHUB_TOKEN`: The PAT required to POST state `pending` statuses onto a commit hash so we don't trigger Julian twice.
- `JULES_API_KEY`: The API credential hitting `https://jules.googleapis.com/v1alpha/sessions`.

## Labeling Parameters (.github/labeler.yml)
Should you need to expand what types of file trigger specific prompts in Jules, map them here:
- `jules:test` triggers aggressive TDD generation for `.ts` and `.py` files.
- `jules:doc` triggers documentation review on `.md` file changes.
- Generic `jules:review` implies clean-code checking on all PR diffs.

## Slash Command Interface
You can trigger specialized Jules workflows by mentioning `@jules` followed by a command in any GitHub comment:

| Command | Action | Description |
|---------|--------|-------------|
| `/ship` | **Ship Work** | Triggers verification, PR creation, and automated merging. |
| `/review`| **Code Review**| Triggers a high-precision architectural and security audit. |
| `/doc` | **Documentation**| Triggers generation/update of READMEs, ARCHITECTURE.md, and MD docs. |
| `/test` | **Test Suite** | Triggers generation of a complete unit test suite for the context. |
| `/fix` | **Auto-Fix** | Triggers analysis and verified code fixing for a reported bug. |
