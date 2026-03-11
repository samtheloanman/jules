---
description: Full Production Deployment Pipeline (Validate -> Sync -> Deploy)
---

# Deploy Pipeline
Run a strict validation, synchronization, and deployment sequence to Vercel Production.

### Usage
Recommend running this when you want to ship `main` to production.

---

### Step 1: Validation
Build the project and run the linting suite to ensures no breaking changes are shipped.

// turbo
1. Build Project
```bash
npm run build
```

// turbo
2. Run Linting & Consistency Checks
```bash
python3 .agent/skills/lint-and-validate/scripts/lint_runner.py
```

---

### Step 2: Synchronization
Ensure the local `main` branch is up to date with the remote to prevent loose states.

// turbo
3. Pull Latest Changes
```bash
git pull origin main
```

---

### Step 3: Production Deployment
Ship the validated code to Vercel.

// turbo
4. Deploy to Production
```bash
vercel --prod
```
