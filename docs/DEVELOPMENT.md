# Development

If you intend on modifying the Cloudflare proxy (`proxy/src/index.ts`) or the Python toolkit (`dispatcher.py`, `jules_helper.py`), follow these loops.

## Python Scripts
These act independently from the edge layer. 

1. Ensure your active Python environment is bound to your IDE. You can execute standard logic mapping:
```bash
python check_gh_jules.py
```

## Cloudflare Proxy

To iterate and debug the edge layer without wasting limits or modifying production:
```bash
cd proxy
```

Ensure your `.dev.vars` file exists within the `proxy/` directory:
```env
GITHUB_TOKEN="ghp_xxx..."
JULES_API_KEY="AQ.xxx..."
```

Run the local wrangler development server:
```bash
npx wrangler dev
```

You can POST mock github payloads mapping `x-github-event: pull_request` to `http://localhost:8787` locally to test your deduplication mapping logic before pushing.
