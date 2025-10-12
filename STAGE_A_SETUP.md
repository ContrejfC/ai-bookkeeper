# Stage A: PostgreSQL + Base Fixtures - Setup Instructions

## Prerequisites

- PostgreSQL 15+ (via Docker or local install)
- Python 3.13+
- Alembic
- psycopg2-binary

## Setup Steps

### 1. Start PostgreSQL

**Option A: Docker Compose (recommended)**
```bash
docker compose up -d postgres
```

**Option B: Docker Desktop**
- Start Docker Desktop
- Open terminal and run:
```bash
docker compose up -d postgres
```

**Option C: Local PostgreSQL**
- Install PostgreSQL 15
- Create database:
```sql
CREATE DATABASE aibookkeeper;
CREATE USER bookkeeper WITH PASSWORD 'bookkeeper_dev_pass';
GRANT ALL PRIVILEGES ON DATABASE aibookkeeper TO bookkeeper;
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

The default DATABASE_URL is already configured for PostgreSQL:
```
DATABASE_URL=postgresql://bookkeeper:bookkeeper_dev_pass@localhost:5432/aibookkeeper
```

### 3. Run Migrations

Generate initial migration (if needed):
```bash
cd ~/ai-bookkeeper
alembic revision --autogenerate -m "Initial schema"
```

Run migrations:
```bash
alembic upgrade head
```

### 4. Verify PostgreSQL Health

```bash
# Quick smoke test (ops-friendly, no API required)
python scripts/db_smoke.py

# Via docker
docker compose exec postgres pg_isready -U bookkeeper -d aibookkeeper

# Via psql
psql -h localhost -U bookkeeper -d aibookkeeper -c "SELECT version();"
```

**Expected db_smoke.py output:**
```
================================================================================
DATABASE SMOKE TEST
================================================================================

Database URL: postgresql://bookkeeper:****@localhost:5432/aibookkeeper
Database type: postgresql

Attempting connection...

--------------------------------------------------------------------------------
RESULTS
--------------------------------------------------------------------------------

✅ DB connection: OK
✅ SELECT 1: OK (returned 1)
✅ Database type: postgresql
✅ Connection time: 0.12s
✅ PostgreSQL version: PostgreSQL 15.x

================================================================================
DATABASE SMOKE TEST: PASSED ✅
================================================================================
```

### 5. Generate Fixtures

```bash
python scripts/generate_stage_a_fixtures.py
```

This will create:
- `tests/fixtures/tenant_alpha_txns.csv` (1,200+ transactions)
- `tests/fixtures/tenant_beta_txns.csv` (1,200+ transactions)
- `tests/fixtures/FIXTURE_SEEDS.md` (seed documentation)

## Acceptance Criteria

- ✅ PostgreSQL health check passes
- ✅ Alembic migrations at head
- ✅ Fixtures committed (2,400+ total transactions)
- ✅ PSI threshold = 0.20 in config/settings.py
- ✅ .env.example updated with PostgreSQL config

## Artifacts

- `docker-compose.yml` - PostgreSQL service definition
- `.env.example` - Updated environment template
- `config/settings.py` - PostgreSQL support + PSI threshold
- `app/db/session.py` - Connection pooling
- `app/db/migrations/` - Alembic setup
- `tests/fixtures/` - Fixture CSVs + seeds
- `STAGE_A_SETUP.md` - This file

## Troubleshooting

**Docker not available:**
- Install Docker Desktop for Mac
- Or use Colima: `brew install colima && colima start`

**Connection refused:**
- Check PostgreSQL is running: `docker compose ps`
- Check logs: `docker compose logs postgres`
- Verify port 5432 is not in use: `lsof -i :5432`

**Migration errors:**
- Reset database: `docker compose down -v && docker compose up -d postgres`
- Wait for health check: `docker compose exec postgres pg_isready`
- Retry migration: `alembic upgrade head`

