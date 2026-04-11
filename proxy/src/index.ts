interface Env {
  GITHUB_TOKEN: string;
  JULES_API_KEY: string;
  GITHUB_WEBHOOK_SECRET: string;
}

async function verifySignature(secret: string, header: string, payload: string): Promise<boolean> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify']
  );
  
  const signatureBytes = new Uint8Array(header.replace(/^sha256=/, '').match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []);
  const payloadBytes = enc.encode(payload);

  return await crypto.subtle.verify('HMAC', key, signatureBytes, payloadBytes);
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }
    
    const event = request.headers.get('x-github-event');
    if (event !== 'pull_request') {
      return new Response('Unhandled Event', { status: 200 });
    }

    const signatureHeader = request.headers.get('x-hub-signature-256');
    if (!signatureHeader) {
      return new Response('Missing Signature', { status: 401 });
    }

    const payloadText = await request.clone().text();
    const isValid = await verifySignature(env.GITHUB_WEBHOOK_SECRET, signatureHeader, payloadText);

    if (!isValid) {
      return new Response('Invalid Signature', { status: 401 });
    }

    try {
      const payload: any = await request.json();
      const action = payload.action;

      if (!['opened', 'synchronize', 'reopened'].includes(action)) {
        return new Response('Ignored action', { status: 200 });
      }

      const prNumber = payload.pull_request.number;
      const repoUrl = payload.repository.html_url;
      const repoName = payload.repository.full_name;
      const labels = payload.pull_request.labels.map((l: any) => l.name);

      // Check for Jules labels
      const hasJulesLabel = labels.some((l: string) => l.startsWith('jules:'));
      if (!hasJulesLabel) {
        return new Response('No Jules label detected', { status: 200 });
      }

      const sha = payload.pull_request.head.sha;

      // 1. Check existing commit status
      const statusCheckRes = await fetch(`https://api.github.com/repos/${repoName}/statuses/${sha}`, {
        headers: {
          'Authorization': `token ${env.GITHUB_TOKEN}`,
          'User-Agent': 'Cloudflare-Worker'
        }
      });
      
      const statuses: any = await statusCheckRes.json();
      const alreadyPending = statuses.some((s: any) => s.context === 'Jules Review' && s.state === 'pending');
      if (alreadyPending) {
        return new Response('Jules is already running on this commit', { status: 200 });
      }

      // 2. Mark status as pending
      await fetch(`https://api.github.com/repos/${repoName}/statuses/${sha}`, {
        method: 'POST',
        headers: {
          'Authorization': `token ${env.GITHUB_TOKEN}`,
          'User-Agent': 'Cloudflare-Worker',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          state: 'pending',
          context: 'Jules Review',
          description: 'Jules is analyzing this code.'
        })
      });

      let prompt = "Please review this PR diff for clean code and security vulnerabilities, and add inline comments if applicable. If you encounter bugs, refer to checklist.py for the full test suite.";
      if (labels.includes('jules:test')) {
         prompt = "Please read this PR diff and generate comprehensive unit tests to cover the newly added code. Do not push until tests pass.";
      } else if (labels.includes('jules:doc')) {
         prompt = "Please read this PR diff and generate comprehensive documentation (markdown and code comments) for the newly added code.";
      }

      // 3. Trigger Jules Session
      ctx.waitUntil(triggerJulesAPI(env.JULES_API_KEY, repoUrl, prNumber, prompt));

      return new Response('Jules Triggered', { status: 202 });
    } catch (e: any) {
      return new Response(e.message, { status: 500 });
    }
  }
};

async function triggerJulesAPI(apiKey: string, repoUrl: string, prNumber: number, prompt: string) {
  // Call Jules REST API (experimental v1alpha)
  await fetch('https://jules.googleapis.com/v1alpha/sessions', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${apiKey}`,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       projectUrl: repoUrl,
       context: `Pull Request #${prNumber}`,
       initialMessage: prompt
     })
  });
}
