---
description: Run full validation suite (lint, build, test) before committing.
---

# /validate - Automated Quality Gate

$ARGUMENTS

---

## Purpose

Enforce code quality by running a mandatory sequence of checks before allowing a commit. This prevents bugs and waste by ensuring all code is "green."

---

## The Protocol

1.  **Format & Lint**: Ensure code style and catch static errors.
2.  **Type Check**: Validate strict type safety (TypeScript).
3.  **Test**: Run unit and integration tests.
4.  **Build**: Verify production build success.

---

## Workflow Steps

### 1. Static Analysis
// turbo
```bash
npm run lint
```
*If this fails, STOP. fix lint errors.*

### 2. Type Verification
// turbo
```bash
npx tsc --noEmit
```
*If this fails, STOP. Fix TypeScript errors.*

### 3. Testing
// turbo
```bash
npm test -- --passWithNoTests
```
*If this fails, STOP. Fix regression errors.*

### 4. Build Verification (The "it compiles" check)
// turbo
```bash
npm run build
```
*If this fails, STOP. The app is broken.*

---

## Usage

Run this command before `git commit`:

```
/validate
```

If all steps pass, you are clear to commit.
