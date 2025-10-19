# 🔧 Render Deployment Troubleshooting Guide

**Issue:** Alembic migration chain broken, preventing database initialization  
**Root Cause:** Missing revision '001' in migration chain  
**Impact:** Fresh deployments will fail during database setup

## 🚨 Primary Issue: Alembic Migration Chain

### Error Details
```bash
$ alembic heads
KeyError: '001'
```

### Root Cause Analysis
- Migration `002_tenant_settings.py` references `down_revision = '001_initial_schema'`
- But `001_initial_schema.py` has `revision = '001_initial_schema'` (not '001')
- Alembic cannot resolve the migration chain

### Fix Required
Update `alembic/versions/001_initial_schema.py`:
```python
# Change from:
revision = '001_initial_schema'

# To:
revision = '001'
```

## 🛠️ Render Settings (Copy/Paste Ready)

### API Service Configuration
```
Service Name: ai-bookkeeper-api
Runtime: Docker
Dockerfile Path: ./Dockerfile.api
Branch: main
Health Check Path: /healthz
Plan: Starter

Environment Variables:
- ENV=production
- BASE_URL=https://ai-bookkeeper-api.onrender.com
- PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
- LOG_LEVEL=INFO
- CORS_ALLOWED_ORIGINS=https://ai-bookkeeper.onrender.com,https://ai-bookkeeper-web.onrender.com
- JWT_SECRET=[GENERATE: openssl rand -hex 32]
- CSRF_SECRET=[GENERATE: openssl rand -hex 32]
- DATABASE_URL=[FROM DATABASE LINK]
- STRIPE_SECRET_KEY=[FROM STRIPE DASHBOARD]
- STRIPE_PUBLISHABLE_KEY=[FROM STRIPE DASHBOARD]
- STRIPE_WEBHOOK_SECRET=[FROM STRIPE DASHBOARD]
- STRIPE_PRICE_STARTER=[FROM STRIPE BOOTSTRAP]
- STRIPE_PRICE_PRO=[FROM STRIPE BOOTSTRAP]
- STRIPE_PRICE_FIRM=[FROM STRIPE BOOTSTRAP]
- QBO_CLIENT_ID=[FROM INTUIT DEVELOPER]
- QBO_CLIENT_SECRET=[FROM INTUIT DEVELOPER]
- QBO_REDIRECT_URI=https://ai-bookkeeper.onrender.com/api/auth/qbo/callback
- QBO_SCOPES=com.intuit.quickbooks.accounting
- QBO_BASE=https://sandbox-quickbooks.api.intuit.com
- QBO_ENVIRONMENT=sandbox
- FREE_PROPOSE_CAP_DAILY=50
- AUTOPOST=false
- ENABLE_LABELS=true
- LABEL_SALT_ROUNDS=12
```

### Web Service Configuration
```
Service Name: ai-bookkeeper-web
Runtime: Docker
Dockerfile Path: ./Dockerfile.web
Branch: main
Health Check Path: /healthz
Plan: Starter

Environment Variables (Mark "Available during build"):
- NEXT_PUBLIC_API_URL=https://ai-bookkeeper-api.onrender.com
- NEXT_PUBLIC_BASE_URL=https://ai-bookkeeper.onrender.com
```

### Database Configuration
```
Database Name: ai-bookkeeper-db
Database Name: ai_bookkeeper
Region: Oregon
Plan: Starter
IP Allow List: []
```

## 🔄 Deployment Steps

### 1. Fix Alembic Baseline
```bash
# Edit alembic/versions/001_initial_schema.py
# Change revision = '001_initial_schema' to revision = '001'
# Commit and push
```

### 2. Create Services in Render
1. **Create Database:**
   - New → PostgreSQL
   - Name: `ai-bookkeeper-db`
   - Plan: Starter
   - Create Database

2. **Create API Service:**
   - New → Web Service
   - Connect GitHub: `ContrejfC/ai-bookkeeper`
   - Name: `ai-bookkeeper-api`
   - Runtime: Docker
   - Dockerfile Path: `./Dockerfile.api`
   - Health Check Path: `/healthz`
   - Link Database: `ai-bookkeeper-db`
   - Set Environment Variables (see above)
   - Create Web Service

3. **Create Web Service:**
   - New → Web Service
   - Connect GitHub: `ContrejfC/ai-bookkeeper`
   - Name: `ai-bookkeeper-web`
   - Runtime: Docker
   - Dockerfile Path: `./Dockerfile.web`
   - Health Check Path: `/healthz`
   - Set Environment Variables (see above)
   - Mark NEXT_PUBLIC_* as "Available during build"
   - Create Web Service

### 3. Verify Deployment
```bash
# Check API health
curl https://ai-bookkeeper-api.onrender.com/healthz

# Check Web health
curl https://ai-bookkeeper-web.onrender.com/healthz

# Check OpenAPI
curl https://ai-bookkeeper-web.onrender.com/openapi.json | jq '.info.version'
```

## 🚨 Common Failure Modes

### 1. Database Connection Failed
- **Cause:** DATABASE_URL not set or incorrect
- **Fix:** Link database to API service in Render Dashboard

### 2. Build Failed - Missing Dependencies
- **Cause:** Docker build issues
- **Fix:** Check Dockerfile paths, ensure all files copied

### 3. Health Check Failed
- **Cause:** Service not binding to $PORT
- **Fix:** Verify CMD in Dockerfile uses ${PORT:-8000}

### 4. Migration Failed
- **Cause:** Alembic chain broken
- **Fix:** Apply the revision fix above

## 📋 Pre-Deployment Checklist

- [ ] Alembic migration chain fixed
- [ ] All environment variables set in Render
- [ ] Database linked to API service
- [ ] NEXT_PUBLIC_* marked "Available during build"
- [ ] Health check paths set to /healthz
- [ ] Stripe keys configured (TEST mode initially)
- [ ] QBO credentials configured (Sandbox initially)

## 🔄 Post-Deployment Verification

1. **Health Checks Pass:**
   ```bash
   curl https://ai-bookkeeper-api.onrender.com/healthz
   curl https://ai-bookkeeper-web.onrender.com/healthz
   ```

2. **Database Migrations Applied:**
   - Check API logs for "Database migrations completed"

3. **OpenAPI Accessible:**
   ```bash
   curl https://ai-bookkeeper-web.onrender.com/openapi.json
   ```

4. **GPT Actions Discovery:**
   ```bash
   curl https://ai-bookkeeper-web.onrender.com/actions
   ```

## 🎯 Success Criteria

- [ ] Both services show "Live" status
- [ ] Health checks return 200 OK
- [ ] Database migrations completed successfully
- [ ] OpenAPI accessible at /openapi.json
- [ ] GPT Actions discovery endpoint working
- [ ] No critical errors in service logs
