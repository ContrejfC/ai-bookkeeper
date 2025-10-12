# Pilot PostgreSQL Migration Guide

This guide walks through migrating from SQLite demo to PostgreSQL for pilot deployments.

## Overview

- **Demo mode:** SQLite (`ai_bookkeeper_demo.db`)
- **Pilot/Production:** PostgreSQL with proper connection pooling and ACID guarantees

## Prerequisites

1. PostgreSQL 13+ installed and running
2. Database created: `CREATE DATABASE ai_bookkeeper_pilot;`
3. User with full privileges: `CREATE USER bookkeeper WITH PASSWORD 'secure_password';`
4. Grant access: `GRANT ALL PRIVILEGES ON DATABASE ai_bookkeeper_pilot TO bookkeeper;`

## Step 1: Configure DATABASE_URL

Update your `.env` file:

```bash
# For pilot/production (PostgreSQL)
DATABASE_URL=postgresql://bookkeeper:secure_password@localhost:5432/ai_bookkeeper_pilot

# Assessment mode (optional)
UI_ASSESSMENT=0
AUTOPOST_ENABLED=false
AUTOPOST_THRESHOLD=0.90
```

**Format:** `postgresql://[user]:[password]@[host]:[port]/[database]`

**For cloud deployments:**
- **AWS RDS:** `postgresql://user:pass@your-instance.region.rds.amazonaws.com:5432/dbname`
- **Google Cloud SQL:** `postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance`
- **Heroku:** Use `DATABASE_URL` from config vars (automatically set)

## Step 2: Run Alembic Migrations

```bash
cd ~/ai-bookkeeper

# Install alembic if not already installed
pip3 install alembic

# Run all migrations
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_rules_versioning
INFO  [alembic.runtime.migration] Running upgrade 002_rules_versioning -> 003_wave2_tenants
INFO  [alembic.runtime.migration] Running upgrade 003_wave2_tenants -> 004_billing
INFO  [alembic.runtime.migration] Running upgrade 004_billing -> 005_notifications
INFO  [alembic.runtime.migration] Running upgrade 005_notifications -> 006_receipt_fields
INFO  [alembic.runtime.migration] Running upgrade 006_receipt_fields -> 007_auth_hardening
INFO  [alembic.runtime.migration] Running upgrade 007_auth_hardening -> 008_xero_export
```

## Step 3: Migrate Sample Data (Optional)

### Option A: Seed Fresh Demo Data

```bash
# Create pilot tenants with clean data
python3 scripts/seed_demo_data.py
python3 scripts/seed_demo_receipts.py
```

### Option B: Migrate from SQLite

```bash
# Export SQLite data
sqlite3 ai_bookkeeper_demo.db .dump > demo_export.sql

# Import to PostgreSQL (requires manual conversion)
# SQLite SQL is not directly compatible with PostgreSQL
# Use a conversion tool or manual migration script
```

**Note:** Option A (fresh seed) is recommended for pilots as it ensures clean, consistent data.

## Step 4: Verify Database Connection

```bash
# Test database connectivity
python3 <<'EOF'
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("✅ PostgreSQL Connected:")
    print(f"   {result.scalar()}")
    
    # Check tables
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_catalog.pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """))
    tables = [row[0] for row in result]
    print(f"\n✅ Tables created: {len(tables)}")
    for table in tables:
        print(f"   • {table}")
EOF
```

## Step 5: Start Application with PostgreSQL

```bash
# Start server (will use DATABASE_URL from .env)
python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Verify health check
curl http://localhost:8000/healthz | jq .

# Expected: {"status":"ok", "database_status":"healthy", ...}
```

## Step 6: Verify /readyz Endpoint

```bash
curl http://localhost:8000/readyz | jq .
```

**Expected response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "migrations": "ok",
    "dependencies": "ok"
  },
  "timestamp": "2025-10-11T19:00:00.000000"
}
```

## Pilot-Specific Configuration

For pilot tenants, ensure the following settings:

```python
# app/db/models.py → TenantSettingsDB defaults
autopost_enabled = False    # Must be False for pilots
autopost_threshold = 0.90   # High confidence threshold
llm_tenant_cap_usd = 50.0   # Budget cap for LLM calls
```

**Create pilot tenants:**
```bash
# Use onboarding wizard or create directly
python3 <<'EOF'
from app.db.session import engine
from app.db.models import TenantSettingsDB
from sqlalchemy.orm import Session

with Session(engine) as db:
    for tenant_id in ["pilot-smb-001", "pilot-prof-002", "pilot-firm-003"]:
        settings = TenantSettingsDB(
            tenant_id=tenant_id,
            autopost_enabled=False,  # ← Critical for pilots
            autopost_threshold=0.90,
            llm_tenant_cap_usd=50.0,
            updated_by="system"
        )
        db.add(settings)
    db.commit()
    print("✅ Pilot tenants configured")
EOF
```

## Monitoring & Maintenance

### Connection Pool Settings

Update `app/db/session.py` for production:

```python
engine_kwargs = {
    "pool_pre_ping": True,      # Test connections before use
    "pool_size": 20,             # Concurrent connections
    "max_overflow": 40,          # Additional connections under load
    "pool_recycle": 3600,        # Recycle connections every hour
    "echo": False,               # Disable SQL logging in production
}
```

### Backup Strategy

```bash
# Daily backups
pg_dump -h localhost -U bookkeeper ai_bookkeeper_pilot > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U bookkeeper ai_bookkeeper_pilot < backup_20251011.sql
```

### Performance Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'ai_bookkeeper_pilot';

-- Monitor query performance
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Troubleshooting

### Issue: "FATAL: password authentication failed"

**Solution:** Verify PostgreSQL user credentials and `pg_hba.conf` settings.

```bash
# Check pg_hba.conf (usually in /etc/postgresql/*/main/)
sudo grep -v "^#" /etc/postgresql/13/main/pg_hba.conf | grep -v "^$"

# Should have line like:
# host    all             all             127.0.0.1/32            md5
```

### Issue: "connection refused"

**Solution:** Ensure PostgreSQL is running and listening on the correct port.

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check listening ports
sudo netstat -tlnp | grep 5432
```

### Issue: "could not connect to server"

**Solution:** Verify DATABASE_URL format and firewall rules.

```bash
# Test connection directly
psql -h localhost -U bookkeeper -d ai_bookkeeper_pilot

# Check if DATABASE_URL is set
echo $DATABASE_URL
```

## Rollback to SQLite

If needed, revert to SQLite:

```bash
# Update .env
echo "DATABASE_URL=sqlite:///./ai_bookkeeper_demo.db" > .env

# Recreate tables
python3 scripts/demo_reset.py

# Restart server
python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## Summary

| Step | Command | Status Check |
|------|---------|--------------|
| 1. Configure | Edit `.env` | `echo $DATABASE_URL` |
| 2. Migrate | `alembic upgrade head` | Check output for errors |
| 3. Seed Data | `python3 scripts/seed_demo_data.py` | Verify tenant created |
| 4. Verify | `python3 -c "from app.db.session import engine..."` | Should print PostgreSQL version |
| 5. Start | `uvicorn app.api.main:app --port 8000` | `curl /healthz` returns 200 |
| 6. Check | `curl /readyz` | All checks return "ok" |

## Next Steps

1. ✅ Complete database migration
2. ✅ Verify all pilot tenants have `AUTOPOST=false`
3. ✅ Configure monitoring (Datadog, New Relic, or built-in `/metrics`)
4. ✅ Set up automated backups
5. ✅ Review security (TLS, firewall, secrets management)
6. ✅ Load test with expected pilot traffic

For questions or issues, refer to the main documentation or contact the engineering team.

