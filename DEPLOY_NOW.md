# 🚀 DEPLOY NOW - Quick Reference Card

**Time to deploy:** ~10 minutes  
**Target:** Render (Docker + Blueprint)  
**Architecture:** Split services (API + Web + DB)

---

## ✅ PRE-FLIGHT CHECK (run locally)

```bash
./ops/pre_deploy_check.sh
```

Expected: ✅ **PRE-DEPLOY CHECK PASSED**

---

## 🎯 RENDER DASHBOARD (5 steps)

### 1️⃣ Apply Blueprint

- **New +** → **Blueprint**
- Repo: `ContrejfC/ai-bookkeeper`
- File: `render-split.yaml`
- **Apply**

Creates: `ai-bookkeeper-api`, `ai-bookkeeper-web`, `ai-bookkeeper-db`

---

### 2️⃣ Web Service Config

**In `ai-bookkeeper-web` → Environment:**

For **each** `NEXT_PUBLIC_*` variable:
- Click **⋮** → ✅ **"Available during build"**

Then: **Manual Deploy**

---

### 3️⃣ API Service Secrets

**Generate locally first:**
```bash
openssl rand -hex 32  # JWT_SECRET
openssl rand -hex 32  # CSRF_SECRET
```

**In `ai-bookkeeper-api` → Environment, add:**
```bash
JWT_SECRET=<paste generated value>
CSRF_SECRET=<paste generated value>
```

Then: **Save Changes** (auto-deploys)

---

### 4️⃣ Wait for Deploy (~5-10 min)

Both services show **"Live"** (green)

---

### 5️⃣ Verify

```bash
# Quick sanity checks:
curl https://ai-bookkeeper-api.onrender.com/healthz
curl https://ai-bookkeeper-web.onrender.com/healthz
curl https://ai-bookkeeper-web.onrender.com/openapi.json | jq '.info.version'
```

**All should return 200 OK**

---

## 🧪 FULL SMOKE TEST

**In Render Shell (`ai-bookkeeper-api` service):**

```bash
# 1. Create API key:
python scripts/create_api_key.py --tenant production --name "Smoke Test"
# Copy output: ak_live_XXXXXXXXXXXXXXXXXXXXXXX
```

**Then locally:**

```bash
./ops/smoke_live.sh \
  --base-url https://ai-bookkeeper-web.onrender.com \
  --api-key ak_live_XXXXXXXXXXXXXXXXXXXXXXX \
  --use-sample-je \
  --spec-version v1.0
```

**Expected:** ✅ **7/7 tests passed**

---

## 🚨 IF BUILD FAILS

**Open Build log and match error:**

| Error | Fix |
|-------|-----|
| `npm ci` fails | Commit `package-lock.json` or use `npm install` |
| `NEXT_PUBLIC_* undefined` | Mark vars **"Available during build"** |
| `server.js not found` | Ensure `output: 'standalone'` in `next.config.js` |
| `alembic` at build time | Move to `CMD` (runtime only) |
| Health check fails | Ensure binding to `$PORT` in both Dockerfiles |

**See full triage:** `docs/RENDER_DEPLOY_QUICKSTART.md`

---

## ✨ SUCCESS CRITERIA

- ✅ Both services "Live" (green)
- ✅ `/healthz` returns 200 on both
- ✅ `/openapi.json` returns valid JSON
- ✅ `smoke_live.sh` passes 7/7
- ✅ API key auth works

---

## 📚 NEXT STEPS

1. **Custom domain:** Web service → Settings → Custom Domain
2. **Stripe webhooks:** `https://ai-bookkeeper-api.onrender.com/billing/webhook`
3. **QBO OAuth:** Redirect URI: `https://ai-bookkeeper-api.onrender.com/auth/qbo/callback`
4. **ChatGPT GPT:** Import `https://ai-bookkeeper-web.onrender.com/openapi.json`

---

## 🆘 NEED HELP?

1. Run pre-flight: `./ops/pre_deploy_check.sh`
2. Check full guide: `docs/RENDER_DEPLOY_QUICKSTART.md`
3. View recent logs: Render Dashboard → Service → Logs tab
4. Compare with local: `docker build -f Dockerfile.api .`

---

**Last updated:** 2025-10-17  
**Deployment architecture:** Split services (API + Web + DB)  
**Total cost:** ~$21/month (Starter instances)
