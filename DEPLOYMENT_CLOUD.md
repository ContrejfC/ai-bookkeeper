# Cloud Staging Deployment Guide

**Target Platforms:** Render.com, Railway.app  
**Stack:** FastAPI + Postgres + Redis + RQ + Tesseract OCR  
**Status:** Production-ready staging configuration

---

## Quick Start

### Option 1: Deploy to Render.com (Recommended)

**Prerequisites:**
- Render.com account
- GitHub repository connected

**Steps:**

1. **Connect Repository**
   - Go to Render Dashboard → New → Blueprint
   - Connect your GitHub repository
   - Render will detect `render.yaml`

2. **Configure Environment Variables**
   - Render will auto-create DATABASE_URL, REDIS_URL
   - Generate JWT_SECRET_KEY: `openssl rand -hex 32`
   - Set OPENAI_API_KEY (optional)
   - Set S3 credentials (optional)

3. **Deploy**
   ```bash
   git push origin main
   # Render auto-deploys on push
   ```

4. **Run Migrations**
   - In Render Shell:
   ```bash
   python3 -m alembic upgrade head
   python3 scripts/seed_demo_data.py
   ```

5. **Verify**
   ```bash
   curl https://your-app.onrender.com/healthz
   curl https://your-app.onrender.com/readyz
   ```

**Estimated Cost:** $17/month
- Web service: $7/month (Starter)
- Worker service: $7/month (Starter)
- Postgres: $7/month (Starter, 1GB)
- Redis: $3/month (25MB)

---

### Option 2: Deploy to Railway.app

**Prerequisites:**
- Railway account
- GitHub repository connected

**Steps:**

1. **Create New Project**
   - Railway Dashboard → New Project → Deploy from GitHub
   - Select your repository

2. **Add Services**
   ```bash
   # In Railway CLI or Dashboard:
   railway add postgres
   railway add redis
   ```

3. **Configure Environment**
   - Railway auto-sets DATABASE_URL, REDIS_URL
   - Add other variables from `.env.staging.example`

4. **Deploy**
   ```bash
   railway up
   ```

5. **Run Migrations**
   ```bash
   railway run python3 -m alembic upgrade head
   railway run python3 scripts/seed_demo_data.py
   ```

6. **Verify**
   ```bash
   curl https://your-app.up.railway.app/healthz
   ```

**Estimated Cost:** $10-15/month
- Usage-based pricing
- Postgres + Redis + 2 services

---

## Manual Docker Deployment

If deploying to custom infrastructure (AWS ECS, GCP Cloud Run, DigitalOcean App Platform):

### 1. Build Docker Image

```bash
cd ai-bookkeeper

# Build
docker build -t ai-bookkeeper:staging .

# Test locally
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e JWT_SECRET_KEY=xxx \
  ai-bookkeeper:staging
```

### 2. Push to Registry

```bash
# Docker Hub
docker tag ai-bookkeeper:staging yourusername/ai-bookkeeper:staging
docker push yourusername/ai-bookkeeper:staging

# OR Google Container Registry
docker tag ai-bookkeeper:staging gcr.io/your-project/ai-bookkeeper:staging
docker push gcr.io/your-project/ai-bookkeeper:staging

# OR AWS ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-west-2.amazonaws.com
docker tag ai-bookkeeper:staging 123456789.dkr.ecr.us-west-2.amazonaws.com/ai-bookkeeper:staging
docker push 123456789.dkr.ecr.us-west-2.amazonaws.com/ai-bookkeeper:staging
```

### 3. Deploy to Cloud Platform

**AWS ECS/Fargate:**
- Create ECS cluster
- Define task definition with Docker image
- Create service with 1+ tasks
- Configure load balancer for HTTPS

**GCP Cloud Run:**
```bash
gcloud run deploy ai-bookkeeper-staging \
  --image gcr.io/your-project/ai-bookkeeper:staging \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,REDIS_URL=...
```

**DigitalOcean App Platform:**
- Create new app from Docker image
- Configure environment variables
- Add managed Postgres and Redis add-ons

---

## Post-Deployment Checklist

### A) Database & Migrations

```bash
# Verify connection
curl https://your-app.com/healthz | jq .database_status
# Expected: "healthy"

# Check migration version
curl https://your-app.com/readyz | jq .checks.migrations
# Expected: "ok"

# If migrations not applied, run:
# (in Render Shell, Railway CLI, or Docker exec)
python3 -m alembic upgrade head
```

### B) Seed Pilot Tenants

```bash
# Seed demo data
python3 scripts/seed_demo_data.py

# Verify tenants created
curl -X GET https://your-app.com/api/tenants \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" | jq .
```

### C) Test Key Endpoints

```bash
# Health checks
curl https://your-app.com/healthz
curl https://your-app.com/readyz

# Login (get JWT)
curl -X POST https://your-app.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@pilot-smb-001.demo","password":"demo-password-123"}' | jq .access_token

# Review page
curl https://your-app.com/review

# Receipts with OCR
curl https://your-app.com/api/receipts?tenant_id=pilot-smb-001

# Analytics
curl https://your-app.com/api/analytics/last7
```

### D) Verify Safety Controls

```bash
# Check tenant settings
curl https://your-app.com/api/tenants/pilot-smb-001/settings \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .

# Expected:
# {
#   "autopost_enabled": false,
#   "autopost_threshold": 0.90,
#   "llm_tenant_cap_usd": 50
# }
```

### E) Test Background Jobs

```bash
# Trigger an async job (e.g., export)
curl -X POST https://your-app.com/api/export/qbo \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"tenant_id":"pilot-smb-001"}'

# Check RQ worker logs in platform dashboard
# Should see job processing
```

### F) Schedule Analytics Rollup

**Render:**
- Cron job already configured in `render.yaml`
- Runs daily at 2:00 AM UTC

**Railway:**
```bash
# Add to Railway cron jobs or use external scheduler (GitHub Actions)
```

**Manual Trigger:**
```bash
python3 jobs/analytics_rollup.py
```

---

## S3 Configuration (Optional)

### Setup AWS S3

1. **Create Bucket**
   ```bash
   aws s3 mb s3://ai-bookkeeper-staging
   ```

2. **Create IAM User**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::ai-bookkeeper-staging",
           "arn:aws:s3:::ai-bookkeeper-staging/*"
         ]
       }
     ]
   }
   ```

3. **Set Environment Variables**
   ```bash
   S3_BUCKET=ai-bookkeeper-staging
   S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
   S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

4. **Verify**
   ```bash
   curl https://your-app.com/api/storage/info
   # Expected: {"backend": "s3", "s3_bucket": "ai-bookkeeper-staging"}
   ```

### Alternative: DigitalOcean Spaces

```bash
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
S3_BUCKET=ai-bookkeeper-staging
S3_ACCESS_KEY_ID=DO00xxx
S3_SECRET_ACCESS_KEY=xxx
```

### Alternative: Backblaze B2

```bash
S3_ENDPOINT=https://s3.us-west-002.backblazeb2.com
S3_BUCKET=ai-bookkeeper-staging
S3_ACCESS_KEY_ID=002xxx
S3_SECRET_ACCESS_KEY=xxx
```

---

## Security Checklist

- [x] HTTPS enabled (automatic on Render/Railway)
- [x] JWT_SECRET_KEY generated (32+ bytes)
- [x] CSRF protection enabled (automatic in middleware)
- [x] CORS restricted to staging domain
- [x] Database credentials secret (auto-generated)
- [x] Redis credentials secret (auto-generated)
- [x] No PII in logs (enforced by analytics sink)
- [x] Rate limiting on auth endpoints (implemented)
- [x] CSP/HSTS headers (implemented in middleware)
- [x] AUTOPOST disabled (hardcoded false for staging)

---

## Monitoring & Logs

### Render

```bash
# View logs in real-time
render logs -s ai-bookkeeper-web-staging --tail

# View metrics
# Dashboard → Service → Metrics tab
```

### Railway

```bash
# View logs
railway logs

# View metrics
# Dashboard → Service → Metrics tab
```

### Health Check Monitoring

Set up external monitoring (e.g., UptimeRobot, Pingdom):

- **Endpoint:** `https://your-app.com/healthz`
- **Interval:** 5 minutes
- **Expected:** Status 200, `{"status":"ok"}`

---

## Performance Targets

| Metric | Target | Monitoring |
|--------|--------|------------|
| /healthz response | <100ms | Platform metrics |
| /review page load | <300ms p95 | APM tool |
| /api/receipts | <500ms p95 | APM tool |
| Worker job throughput | >10 jobs/min | RQ dashboard |
| Database connections | <20 active | Postgres metrics |
| Redis memory | <20MB | Redis metrics |

---

## Troubleshooting

### Health Check Fails

```bash
# Check logs
render logs -s ai-bookkeeper-web-staging --tail 100

# Common issues:
# - DATABASE_URL not set → Check environment variables
# - Migrations not applied → Run alembic upgrade head
# - Tesseract not installed → Verify Dockerfile apt-get install
```

### Worker Not Processing Jobs

```bash
# Check worker logs
render logs -s ai-bookkeeper-worker-staging --tail 100

# Verify Redis connection
redis-cli -u $REDIS_URL ping
# Expected: PONG

# Check RQ queue
python3 -c "from rq import Queue; from redis import Redis; q = Queue(connection=Redis.from_url('$REDIS_URL')); print(len(q))"
```

### S3 Upload Fails

```bash
# Test AWS credentials
aws s3 ls s3://ai-bookkeeper-staging --profile your-profile

# Check environment variables
env | grep S3_

# Test presigned URL
curl https://your-app.com/api/receipts/123/fields
# Should include presigned URL if S3 configured
```

### Migration Fails

```bash
# Check current version
python3 -m alembic current

# Rollback one version
python3 -m alembic downgrade -1

# Re-apply
python3 -m alembic upgrade head

# If stuck, manually inspect database
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

---

## Cost Optimization

### Render

- **Starter Plan:** $7/service (good for staging)
- **Upgrade to Standard ($25) if:**
  - Need >0.5 CPU
  - Need >512MB RAM
  - Need faster cold start

### Railway

- **Usage-based pricing:** Pay for what you use
- **Optimize:**
  - Scale down worker replicas during low traffic
  - Use smaller Postgres plan for staging
  - Set Redis maxmemory policy to `allkeys-lru`

### S3

- **AWS S3 Standard:** $0.023/GB/month + requests
- **Consider Glacier for old artifacts:** $0.004/GB/month
- **Or use DigitalOcean Spaces:** $5/month for 250GB

---

## Next Steps

1. **Deploy to Staging:** Follow Quick Start above
2. **Run Acceptance Tests:** See `PILOT_READINESS_COMPLETE.md`
3. **Capture Screenshots:** See `SCREENSHOT_INSTRUCTIONS.md`
4. **Enable Monitoring:** Set up UptimeRobot or similar
5. **Schedule Analytics:** Verify cron job runs daily
6. **Prep for Production:** Duplicate staging setup with production env vars

---

**Questions?** See troubleshooting section or check platform docs:
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- AWS: https://docs.aws.amazon.com/s3/

**Last Updated:** 2025-10-11  
**Version:** 1.0 (Staging-ready)

