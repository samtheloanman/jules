# Getting Started

## 1. Prerequisites
- A Cloudflare Account (the free tier is 100% fine)
- `node` & `npm` installed for managing the wrangler CLI
- A GitHub Personal Access Token (with `repo` read/write access)
- A Jules API Key (`JULES_API_KEY`) 

## 2. Setting Up the Proxy
Deploy the Cloudflare Worker to act as your webhook listener:

```bash
cd proxy
npm install wrangler -g
```

Then, inject your remote secrets securely:
```bash
echo "YOUR_GITHUB_TOKEN" | npx wrangler secret put GITHUB_TOKEN
echo "YOUR_JULES_API_KEY" | npx wrangler secret put JULES_API_KEY
```

Run deploy:
```bash
npx wrangler deploy
```

## 3. Wire Up GitHub
Cloudflare will assign you a worker URL (e.g., `https://jules-webhook-proxy...workers.dev`).
Take this URL to your GitHub repository -> Settings -> Webhooks.
1. Add a new webhook.
2. Paste the URL.
3. Content-type must be JSON.
4. Select individual events: "Pull Requests" (Opened, Synchronized, Reopened).

## 4. Setting up auto-labels (Optional but Recommended)
GitHub Actions `.github/workflows/jules-labels.yml` relies on the `jules:` labels. The file is already committed to this repository. When you commit new code on PRs, the Github Labeler extension will tag it automatically and the proxy will parse those labels!
