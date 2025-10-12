# 🚀 Deploy AI Bookkeeper to Render (5 Minutes)

**Your Account:** contrejf513@gmail.com  
**GitHub Repo:** https://github.com/ContrejfC/ai-bookkeeper

---

## Step 1: Go to Render Dashboard

**Open in browser:** https://dashboard.render.com/

**Log in** with: contrejf513@gmail.com

---

## Step 2: Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Choose **"Build and deploy from a Git repository"**
4. Click **"Connect account"** if GitHub isn't connected yet

---

## Step 3: Select Your Repository

1. Find: **`ContrejfC/ai-bookkeeper`**
2. Click **"Connect"**

---

## Step 4: Configure Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `ai-bookkeeper-web` |
| **Region** | `Oregon (US West)` or closest to you |
| **Branch** | `main` |
| **Root Directory** | (leave blank) |
| **Runtime** | `Docker` |
| **Docker Command** | (leave blank - will use Dockerfile) |
| **Plan** | `Free` |

---

## Step 5: Environment Variables

Scroll to **"Environment Variables"** section and add:

### Required Variables:

```bash
# Click "Add Environment Variable" for each:

JWT_SECRET_KEY
  → Click "Generate" button (or paste a random 32+ char string)

DATABASE_URL
  → postgresql://user:pass@host/db
  → (We'll add PostgreSQL next)

UI_ASSESSMENT
  → 1

AUTOPOST_ENABLED
  → false

GATING_THRESHOLD
  → 0.90

OCR_PROVIDER
  → tesseract

LOG_LEVEL
  → INFO

SEO_INDEX
  → 0
```

---

## Step 6: Add PostgreSQL Database

1. Scroll down to **"Add Database"** section
2. Click **"New Database"** or **"Add Database"**
3. Select **"PostgreSQL"**
4. Configure:
   - **Name:** `ai-bookkeeper-db`
   - **Plan:** `Free` (256 MB)
   - **Region:** Same as web service
5. Click **"Create Database"**

**Render will automatically link `DATABASE_URL`** to your web service!

---

## Step 7: Deploy!

1. Click **"Create Web Service"** button at bottom
2. Wait 3-5 minutes for deployment
3. Watch the build logs

### What Happens:
- ✅ Builds Docker image with Python + Tesseract
- ✅ Installs dependencies from `requirements.txt`
- ✅ Runs database migrations (`alembic upgrade head`)
- ✅ Starts uvicorn server on port 10000
- ✅ Health check at `/healthz`

---

## Step 8: Get Your URL! 🎉

Once deployed, your URL will be at the top:

**`https://ai-bookkeeper-web-XXXX.onrender.com`**

(XXXX is a random string Render assigns)

---

## Step 9: Test Your Deployment

Open these URLs in your browser:

1. **Home page:** `https://YOUR-URL.onrender.com/`
2. **Health check:** `https://YOUR-URL.onrender.com/healthz`
3. **Readiness:** `https://YOUR-URL.onrender.com/readyz`
4. **Support:** `https://YOUR-URL.onrender.com/support`
5. **Legal pages:** `https://YOUR-URL.onrender.com/legal/terms`

---

## ⚠️ Important Notes

### Free Tier Limitations:
- ⏰ **Cold starts:** Service spins down after 15 min of inactivity
- 💾 **Database:** 256 MB PostgreSQL (90 days expiration)
- 🔄 **No Redis:** Worker/cron services disabled on free tier
- 🚫 **No custom domain:** Use `.onrender.com` subdomain

### First Request May Be Slow:
If the service was asleep, first request takes 30-60 seconds to wake up.

---

## 🎯 What You'll See

Your home page will show:
- ✨ Hero section with "Sign in" CTA
- 📊 How It Works (3 steps)
- ⚡ Features grid (8 cards)
- 🔒 Security badges
- 💰 Pricing teaser
- ❓ FAQ section
- 📝 Footer with legal links

---

## 🔧 Troubleshooting

### Build Fails?
- Check logs in Render dashboard
- Common issue: Missing dependencies in `requirements.txt`

### Health Check Fails?
- Wait 1-2 minutes after deployment
- Check if migrations ran successfully in logs

### Can't Connect to Database?
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running

---

## 🚀 Upgrade to Starter ($7/mo) Later

To enable Worker + Cron services:
1. Upgrade plan to **Starter**
2. Add **Redis** instance ($5/mo)
3. Enable worker and cron in `render.yaml`

---

## 📞 Need Help?

**Deployment failing?** Check:
- GitHub repo is public or Render has access
- `Dockerfile` exists and is valid
- `requirements.txt` is complete

**App not working?** Test locally first:
```bash
cd ~/ai-bookkeeper
python3 -m pytest -v
python3 -m uvicorn app.api.main:app --reload
```

---

**Ready? Go to:** https://dashboard.render.com/ 🚀

