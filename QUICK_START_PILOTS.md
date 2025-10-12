# 🚀 Quick Start: Get Pilots Running (5 Minutes)

Your staging environment is **LIVE** and **READY**. Here's the fastest path to verified pilots:

---

## ✅ 1. Set GitHub Secrets (2 minutes)

Go to: https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions

Click **"New repository secret"** and add these 3:

| Secret Name | Where to Get It |
|-------------|-----------------|
| `STAGING_DATABASE_URL` | Render → ai-bookkeeper-db → Connect → **Internal Database URL** |
| `STAGING_REDIS_URL` | Render → ai-bookkeeper-redis → Connect → **Internal Redis URL** |
| `STAGING_JWT_SECRET_KEY` | Copy from: Render → ai-bookkeeper-web → Environment → `JWT_SECRET_KEY` |

**Quick Copy:**
- Render dashboard: https://dashboard.render.com/
- Just copy-paste the full URLs (they start with `postgresql://` and `redis://`)

---

## ✅ 2. Seed Pilot Data (1 minute)

Go to: https://github.com/ContrejfC/ai-bookkeeper/actions/workflows/seed_pilots.yml

1. Click **"Run workflow"** (right side)
2. Set:
   - `confirm`: `I_UNDERSTAND`
   - `tenant_prefix`: `pilot`
   - `count`: `3`
3. Click green **"Run workflow"** button
4. Wait ~2 minutes
5. Download artifacts when done → verify `db_summary.txt` shows rows created

---

## ✅ 3. Test Login (30 seconds)

Visit: **https://ai-bookkeeper-app.onrender.com/login**

**Credentials:**
- Email: `owner@pilot-smb-001.demo`
- Password: `demo-password-123`

**Expected:** Redirect to `/review` with transaction list

---

## ✅ 4. Verify Health (30 seconds)

Run locally:
```bash
cd ~/ai-bookkeeper
./scripts/verify_staging.sh https://ai-bookkeeper-app.onrender.com
```

**Expected Output:**
```
✅ /healthz returned status: ok
✅ /readyz returned status: ready
✅ Database: healthy
✅ Alembic version: 008_xero_export
```

---

## ✅ 5. Capture Screenshots for Demo (10 minutes - OPTIONAL)

**Automated (Playwright):**
```bash
# In GitHub Actions:
Actions → "UI Screenshots (Playwright)" → Run workflow
# Wait 5 min → Download ui-screenshots.zip (33 PNG files)
```

**Manual (Quick 5 shots):**
1. Login page
2. Review dashboard
3. Receipts page
4. Analytics page
5. Rules console

---

## 🎯 That's It!

Your app is live at: **https://ai-bookkeeper-app.onrender.com**

**Safety confirmed:**
- ✅ AUTOPOST_ENABLED=false (won't auto-post to GL)
- ✅ GATING_THRESHOLD=0.90 (90% confidence required)
- ✅ PII stripping enabled
- ✅ Migrations at head (008_xero_export)

---

## 📋 For Full Verification

See: `STAGING_GO_LIVE_CHECKLIST.md` (complete 8-section checklist)

---

## 🚨 Quick Troubleshooting

**Login fails:** Run the "Seed Pilots" workflow first (step 2)

**Slow first request:** Cold start (free tier) - wait 60s and retry

**503 error:** Service is starting - wait 30s

**Health check fails:** Check Render logs: Dashboard → ai-bookkeeper-web → Logs

---

**Ready for pilots!** 🎉

