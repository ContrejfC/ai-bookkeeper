# Starting the AI Bookkeeper API Server

## Current Status: ERR_CONNECTION_REFUSED ✅ (Expected)

**This is normal!** The `/readyz` endpoint is implemented in the code, but the FastAPI server is not running yet.

---

## Prerequisites (Choose One)

### Option A: With SQLite (Quick Test - No PostgreSQL)
```bash
# Update DATABASE_URL to SQLite temporarily
export DATABASE_URL="sqlite:///./aibookkeeper.db"

# Start the server
cd ~/ai-bookkeeper
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected `/readyz` response (SQLite):**
```json
{
  "ready": true,
  "checks": {
    "database_connect": {"status": "ok"},
    "migrations": {"status": "warning", "message": "Migrations not at head"},
    "write_read_smoke": {"status": "ok"},
    "ocr_stub": {"status": "warning", "message": "expected for Stage A"},
    "vector_store": {"status": "ok", "backend": "none"}
  }
}
```

---

### Option B: With PostgreSQL (Full Stage A Acceptance)

**Step 1: Install Dependencies**
```bash
pip install psycopg2-binary uvicorn fastapi
```

**Step 2: Start PostgreSQL**
```bash
# If Docker is available:
cd ~/ai-bookkeeper
docker compose up -d postgres

# Wait for health check
sleep 10

# OR use local PostgreSQL:
brew install postgresql@15
brew services start postgresql@15
createdb aibookkeeper
psql aibookkeeper -c "CREATE USER bookkeeper WITH PASSWORD 'bookkeeper_dev_pass';"
psql aibookkeeper -c "GRANT ALL PRIVILEGES ON DATABASE aibookkeeper TO bookkeeper;"
```

**Step 3: Run Migrations**
```bash
cd ~/ai-bookkeeper
alembic upgrade head
```

**Step 4: Start API Server**
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Step 5: Test Endpoints**

In a new terminal:
```bash
# Health check (basic)
curl http://localhost:8000/healthz

# Readiness check (comprehensive)
curl http://localhost:8000/readyz
```

**Expected `/readyz` response (PostgreSQL):**
```json
{
  "ready": true,
  "checks": {
    "database_connect": {"status": "ok", "timing_ms": 2.34},
    "migrations": {
      "status": "ok",
      "current": "001_initial_schema",
      "head": "001_initial_schema",
      "timing_ms": 5.67
    },
    "write_read_smoke": {"status": "ok", "timing_ms": 3.89},
    "ocr_stub": {
      "status": "warning",
      "available": false,
      "message": "OCR module not found (expected for Stage A)",
      "timing_ms": 0.12
    },
    "vector_store": {
      "status": "ok",
      "backend": "none",
      "message": "Vector store disabled (as expected)",
      "timing_ms": 0.08
    }
  },
  "total_timing_ms": 12.10,
  "timestamp": "2025-10-11T14:45:00-04:00"
}
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'uvicorn'`
**Solution:**
```bash
pip install uvicorn fastapi
```

### Issue: `ModuleNotFoundError: No module named 'psycopg2'`
**Solution:**
```bash
pip install psycopg2-binary
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)

# Or use a different port
uvicorn app.api.main:app --reload --port 8001
```

### Issue: `/readyz` returns `"ready": false`
**Check which component failed:**
- Look at the `checks` object in the response
- `database_connect: error` → PostgreSQL not running
- `migrations: warning` → Run `alembic upgrade head`
- `write_read_smoke: error` → Database permissions issue

---

## Quick Start for Testing (No PostgreSQL Needed)

If you just want to verify the `/readyz` endpoint works:

```bash
# Terminal 1: Start with SQLite (temporary)
cd ~/ai-bookkeeper
export DATABASE_URL="sqlite:///./aibookkeeper.db"
uvicorn app.api.main:app --reload

# Terminal 2: Test the endpoint
curl http://localhost:8000/readyz | python3 -m json.tool
```

---

## Stage A Full Acceptance (PostgreSQL Required)

For **conditional acceptance → full acceptance**, you need:
1. ✅ PostgreSQL running
2. ✅ `alembic upgrade head` completed
3. ✅ API server started
4. ✅ `/readyz` returns `"ready": true` with migrations at head

**Once these are done, Stage A achieves full acceptance.**

