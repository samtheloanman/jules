# Testing

## The Edge Layer
Testing the Cloudflare Worker currently relies on mock `POST` payloads mimicking the shape built by GitHub Actions. Because there is currently no unit test suite, any major configuration tweaks within `proxy/src/index.ts` should be explicitly deployed to `npx wrangler dev` or a non-production bucket to ensure the routing holds.

## Python Suite checks
For ensuring Jules and Git align perfectly locally:
Run the internal `check_gh_jules.py` validation script. 

When creating pull requests labeled with `jules:test`, Jules will autonomously pull out the untestable modules inside your `.py` logic and spin out full native unit tests without manual intervention.

To utilize this, make sure to read the rules defined in `AGENTS.md` before invoking the bot!
