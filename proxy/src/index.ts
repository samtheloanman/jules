interface Env {
  GITHUB_TOKEN: string;
  JULES_API_KEY: string;
  GITHUB_WEBHOOK_SECRET: string;
  DISCORD_WEBHOOK_URL?: string;
  SLACK_WEBHOOK_URL?: string;
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
    if (!['pull_request', 'issues', 'issue_comment'].includes(event || '')) {
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

      let type = '';
      let number = 0;
      let labels: string[] = [];
      let sha: string | null = null;
      let repoUrl = payload.repository.html_url;
      let repoName = payload.repository.full_name;

      if (event === 'pull_request') {
        if (!['opened', 'synchronize', 'reopened'].includes(action)) {
          return new Response('Ignored action', { status: 200 });
        }
        type = 'Pull Request';
        number = payload.pull_request.number;
        labels = payload.pull_request.labels.map((l: any) => l.name);
        sha = payload.pull_request.head.sha;
      } else if (event === 'issues') {
        if (!['opened', 'edited', 'labeled'].includes(action)) {
          return new Response('Ignored action', { status: 200 });
        }
        type = 'Issue';
        number = payload.issue.number;
        labels = payload.issue.labels.map((l: any) => l.name);
      } else if (event === 'issue_comment') {
        if (!['created'].includes(action)) {
          return new Response('Ignored action', { status: 200 });
        }
        type = payload.issue.pull_request ? 'Pull Request Comment' : 'Issue Comment';
        number = payload.issue.number;
        labels = payload.issue.labels.map((l: any) => l.name);
      }

      // Check for Jules labels
      const hasJulesLabel = labels.some((l: string) => l.startsWith('jules:'));
      if (!hasJulesLabel) {
        return new Response('No Jules label detected', { status: 200 });
      }

      if (sha) {
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
      }

      let prompt = "Please review this code for clean code, security issues, or answer questions.";
      if (labels.includes('jules:test')) {
         prompt = "Please read this context and generate comprehensive unit tests to cover the code. Do not push until tests pass.";
      } else if (labels.includes('jules:doc')) {
         prompt = "Please read this context and generate comprehensive documentation (markdown and code comments) for the code.";
      } else if (event === 'issue_comment' && payload.comment?.body) {
         prompt = `User commented: ${payload.comment.body}\nPlease address this request.`;
      }

      // 3. Trigger Jules Session
      ctx.waitUntil(triggerJulesAPI(env.JULES_API_KEY, repoUrl, number, prompt));

      // 4. Send Notification
      ctx.waitUntil(sendNotification(env, `Jules is processing ${type} #${number} on ${repoName}`));

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
       context: `GitHub Event Context #${prNumber}`,
       initialMessage: prompt
     })
  });
}

async function sendNotification(env: Env, message: string) {
  const promises = [];
  if (env.DISCORD_WEBHOOK_URL) {
    promises.push(fetch(env.DISCORD_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: message })
    }));
  }
  if (env.SLACK_WEBHOOK_URL) {
    promises.push(fetch(env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message })
    }));
  }
  await Promise.allSettled(promises);
}
