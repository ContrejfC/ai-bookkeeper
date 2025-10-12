# 🚀 Deploy to Render - Quick Checklist

**Repository:** https://github.com/ContrejfC/ai-bookkeeper  
**Status:** ✅ Code pushed to GitHub (1,846 files)

---

## Step 1: Sign Up / Log In
- [ ] Go to: https://render.com/
- [ ] Sign up with GitHub (easiest)
- [ ] Verify email

---

## Step 2: Create Resources

### PostgreSQL Database
- [ ] Dashboard → "New +" → "PostgreSQL"
- [ ] Name: `ai-bookkeeper-db`
- [ ] Plan: Free
- [ ] Click "Create Database"
- [ ] Wait ~2 min
- [ ] Copy "Internal Database URL" → Save below:
  ```
  DATABASE_URL = postgresql://...
  ```

### Redis Cache
- [ ] Dashboard → "New +" → "Redis"
- [ ] Name: `ai-bookkeeper-redis`
- [ ] Plan: Free
- [ ] Click "Create Redis"
- [ ] Wait ~1 min
- [ ] Copy "Internal Redis URL" → Save below:
  ```
  REDIS_URL = redis://...
  ```

---

## Step 3: Deploy from Blueprint

- [ ] Dashboard → "New +" → "Blueprint"
- [ ] Repository: `ContrejfC/ai-bookkeeper`
- [ ] Blueprint: `render.yaml` (auto-detected)
- [ ] Click "Apply"

### Environment Variables (paste these when prompted):

```bash
DATABASE_URL = <paste postgres URL from step 2>
REDIS_URL = <paste redis URL from step 2>
JWT_SECRET_KEY = 6997cc3f62be47cb1d0536e7c4e633b05217428e79999ab122d7603a985dde23
PASSWORD_RESET_SECRET = 1ed35239f0f28c8a96f8739922f7c6d2c12d2243d946d5891d334c0037867398
OPENAI_API_KEY = (leave blank or add later)
OCR_PROVIDER = tesseract
AUTOPOST_ENABLED = false
GATING_THRESHOLD = 0.90
UI_ASSESSMENT = 1
```

- [ ] Click "Deploy"

---

## Step 4: Wait for Build (~10 minutes)

Watch the logs in Render dashboard:
- [ ] Docker build completes
- [ ] Migrations run (`alembic upgrade head`)
- [ ] Web service starts (port 10000)
- [ ] Worker service starts
- [ ] Cron service scheduled

---

## Step 5: Verify Deployment

Your URL will be: `https://ai-bookkeeper-web-XXXXX.onrender.com`

- [ ] Visit: `https://your-url/healthz` → Check for `{"status": "ok"}`
- [ ] Visit: `https://your-url/readyz` → Check migration status
- [ ] Visit: `https://your-url/` → Should see login page

---

## Step 6: Seed Demo Data (Optional)

### Option A: GitHub Actions (Easiest)
1. Go to: https://github.com/ContrejfC/ai-bookkeeper/actions
2. Click "Seed Pilots (Staging)"
3. Click "Run workflow"
4. Input: `I_UNDERSTAND`
5. Click "Run workflow"

**Required GitHub Secrets** (Settings → Secrets → Actions):
```
STAGING_DATABASE_URL = <same postgres URL from step 2>
```

### Option B: Render Shell
1. Dashboard → ai-bookkeeper-web → "Shell"
2. Run: `python scripts/seed_demo_data.py`

---

## Default Login Credentials (after seeding)

**Tenant 1 (SMB):**
- Email: `owner@pilot-smb-001.demo`
- Password: `demo-password-123`

**Tenant 2 (Professional):**
- Email: `owner@pilot-prof-002.demo`
- Password: `demo-password-123`

**Tenant 3 (Firm):**
- Email: `owner@pilot-firm-003.demo`
- Password: `demo-password-123`

---

## Troubleshooting

### Build fails?
- Check Dockerfile syntax
- Check requirements.txt for missing packages

### Migrations fail?
- Check DATABASE_URL is correct
- Ensure Postgres is running
- Check logs: `alembic current`

### App won't start?
- Check environment variables are set
- Check port 10000 is exposed
- Check health check endpoint: `/healthz`

### Can't log in?
- Run seed script first (Step 6)
- Check database has users: `SELECT * FROM users;`

---

## Next Steps After Deploy

1. Set up monitoring (Render provides built-in metrics)
2. Add custom domain (optional)
3. Enable HTTPS (Render provides free TLS)
4. Set up GitHub Actions for CI/CD
5. Configure alerts for health checks
6. Review logs for any errors
7. Test all features end-to-end

---

## Support

- Render Docs: https://render.com/docs
- Repository: https://github.com/ContrejfC/ai-bookkeeper
- Issues: https://github.com/ContrejfC/ai-bookkeeper/issues

**Estimated total time: ~30-45 minutes** ⏱️

