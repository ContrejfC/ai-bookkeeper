# Backup & Restore Runbook

**Version:** 1.0  
**Last Updated:** 2024-10-11  
**Owner:** DevOps Team

---

## Overview

This runbook covers daily logical backups and restore procedures for the AI Bookkeeper PostgreSQL database.

---

## Daily Logical Backup

### Automated Cron Job

**Schedule:** Daily at 2:00 AM UTC

**Command:**

```bash
0 2 * * * /usr/local/bin/aibookkeeper_backup.sh
```

### Backup Script

**File:** `/usr/local/bin/aibookkeeper_backup.sh`

```bash
#!/bin/bash
# AI Bookkeeper Daily Backup Script

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/aibookkeeper"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
DATABASE_URL="${DATABASE_URL}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
BACKUP_FILE="$BACKUP_DIR/aibookkeeper_${DATE}.sql.gz"

# Perform logical backup
echo "Starting backup at $(date)"
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    echo "✅ Backup successful: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "❌ Backup failed"
    exit 1
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "aibookkeeper_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "Cleaned up backups older than $RETENTION_DAYS days"

# Upload to S3 (optional)
if command -v aws &> /dev/null; then
    aws s3 cp "$BACKUP_FILE" "s3://aibookkeeper-backups/$(basename $BACKUP_FILE)"
    echo "✅ Uploaded to S3"
fi

echo "Backup completed at $(date)"
```

### Backup Verification

**Daily Verification Check:**

```bash
# List recent backups
ls -lh /backups/aibookkeeper/ | tail -5

# Verify latest backup is not empty
LATEST_BACKUP=$(ls -t /backups/aibookkeeper/aibookkeeper_*.sql.gz | head -1)
if [ -s "$LATEST_BACKUP" ]; then
    echo "✅ Latest backup verified: $LATEST_BACKUP"
    echo "   Size: $(du -h "$LATEST_BACKUP" | cut -f1)"
else
    echo "❌ Latest backup is empty or missing"
    exit 1
fi
```

---

## Restore Procedure

### Pre-Restore Checklist

- [ ] **Stop Application:** Ensure no writes during restore
- [ ] **Identify Backup:** Confirm backup file to restore
- [ ] **Test Environment:** Consider restoring to staging first
- [ ] **Notify Team:** Alert stakeholders of maintenance window

---

### Restore Command

#### 1. Stop Application

```bash
# Stop API server
systemctl stop aibookkeeper

# Stop worker processes
systemctl stop aibookkeeper-worker

# Verify no active connections
psql $DATABASE_URL -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'aibookkeeper';"
```

#### 2. Drop and Recreate Database

```bash
# Connect to postgres database (not aibookkeeper)
psql postgres://user:pass@localhost:5432/postgres

# Drop existing database
DROP DATABASE aibookkeeper;

# Recreate database
CREATE DATABASE aibookkeeper OWNER bookkeeper;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aibookkeeper TO bookkeeper;

# Exit
\q
```

#### 3. Restore from Backup

```bash
# Restore from gzipped backup
gunzip -c /backups/aibookkeeper/aibookkeeper_20241011_020000.sql.gz | psql $DATABASE_URL

# OR restore from S3
aws s3 cp s3://aibookkeeper-backups/aibookkeeper_20241011_020000.sql.gz - | gunzip | psql $DATABASE_URL
```

#### 4. Verify Restore

```bash
# Connect to database
psql $DATABASE_URL

# Check table counts
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

# Verify migrations
SELECT version_num, description 
FROM alembic_version;

# Check latest transaction
SELECT MAX(created_at) 
FROM transactions;

# Exit
\q
```

#### 5. Run Migrations (if needed)

```bash
# Only if restoring to a different schema version
alembic upgrade head
```

#### 6. Restart Application

```bash
# Start API server
systemctl start aibookkeeper

# Start worker processes
systemctl start aibookkeeper-worker

# Verify health
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

---

## Point-in-Time Recovery (PITR)

### Prerequisites

- PostgreSQL Write-Ahead Logging (WAL) archiving enabled
- Continuous archiving to S3 or archive directory

### Enable WAL Archiving

**postgresql.conf:**

```conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /wal_archive/%f && cp %p /wal_archive/%f'
max_wal_senders = 3
```

### PITR Restore

```bash
# Stop PostgreSQL
systemctl stop postgresql

# Remove existing data directory
rm -rf /var/lib/postgresql/15/main/*

# Restore base backup
tar -xzf /backups/base_backup.tar.gz -C /var/lib/postgresql/15/main/

# Create recovery.conf (PostgreSQL 12+)
cat > /var/lib/postgresql/15/main/recovery.signal << EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '2024-10-11 14:30:00'
EOF

# Start PostgreSQL (will apply WAL logs until target time)
systemctl start postgresql
```

---

## Disaster Recovery Scenarios

### Scenario 1: Accidental Data Deletion

**Symptoms:**
- User reports missing transactions
- Specific tenant data deleted

**Recovery:**

```bash
# 1. Identify deletion time from audit logs
psql $DATABASE_URL -c "SELECT * FROM audit_log WHERE action='DELETE' ORDER BY timestamp DESC LIMIT 10;"

# 2. Find last good backup before deletion
ls -lt /backups/aibookkeeper/ | grep "$(date -d '2024-10-10' +%Y%m%d)"

# 3. Restore to staging for selective data recovery
# (Then export specific tenant data and reimport to production)
```

### Scenario 2: Database Corruption

**Symptoms:**
- PostgreSQL errors
- Cannot connect to database
- Data integrity issues

**Recovery:**

```bash
# 1. Stop application immediately
systemctl stop aibookkeeper

# 2. Verify database state
psql $DATABASE_URL -c "SELECT pg_database_size('aibookkeeper');"

# 3. If corruption confirmed, restore from latest backup
# (Follow full restore procedure above)
```

### Scenario 3: Full System Failure

**Symptoms:**
- Entire server down
- Database unreachable

**Recovery:**

```bash
# 1. Provision new server
# 2. Install PostgreSQL 15
# 3. Restore from S3 backup
aws s3 cp s3://aibookkeeper-backups/aibookkeeper_latest.sql.gz - | gunzip | psql $DATABASE_URL

# 4. Update DNS/load balancer
# 5. Verify health endpoints
```

---

## Backup Testing

### Monthly Restore Test

**Schedule:** First Sunday of each month

**Procedure:**

```bash
# 1. Provision test instance
docker run -d --name postgres-restore-test -e POSTGRES_PASSWORD=test postgres:15-alpine

# 2. Restore latest backup
gunzip -c /backups/aibookkeeper/aibookkeeper_latest.sql.gz | \
    psql postgresql://postgres:test@localhost:5432/postgres

# 3. Verify table counts match production
# 4. Document test results
# 5. Cleanup test instance
docker rm -f postgres-restore-test
```

---

## Backup Monitoring

### Alerts

**Configure alerts for:**

1. **Backup Failure:**
   - Trigger: Backup script exits with non-zero code
   - Channel: PagerDuty + Slack

2. **Backup Size Anomaly:**
   - Trigger: Backup size differs >20% from previous day
   - Channel: Slack

3. **Missing Backup:**
   - Trigger: No backup file created in last 25 hours
   - Channel: PagerDuty

### Monitoring Dashboard

**Grafana Dashboard:**

```promql
# Backup success rate (last 7 days)
sum(rate(backup_success_total[7d])) / sum(rate(backup_attempts_total[7d]))

# Average backup size
avg(backup_size_bytes) by (day)

# Time since last backup
time() - backup_last_success_timestamp
```

---

## Backup Encryption

### Encrypted Backups (Production)

**Using GPG:**

```bash
# Backup with encryption
pg_dump $DATABASE_URL | gzip | gpg --encrypt --recipient ops@example.com > backup_encrypted.sql.gz.gpg

# Restore with decryption
gpg --decrypt backup_encrypted.sql.gz.gpg | gunzip | psql $DATABASE_URL
```

---

## Retention Policy

| Backup Type | Retention Period | Storage Location |
|-------------|------------------|------------------|
| **Daily** | 30 days | Local + S3 |
| **Weekly** | 90 days | S3 |
| **Monthly** | 1 year | S3 Glacier |
| **Yearly** | 7 years | S3 Glacier Deep Archive |

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| **Database Admin** | DevOps Team | devops@example.com |
| **On-Call Engineer** | PagerDuty | — |
| **Backup System** | AWS Support | support.aws.amazon.com |

---

## Appendix: Useful Commands

### Check Database Size

```bash
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('aibookkeeper'));"
```

### List All Tables

```bash
psql $DATABASE_URL -c "\dt"
```

### Export Single Tenant

```bash
psql $DATABASE_URL -c "COPY (SELECT * FROM transactions WHERE tenant_id='pilot-acme-corp') TO STDOUT WITH CSV HEADER" > tenant_export.csv
```

### Verify Backup Integrity

```bash
# Check if backup is valid gzip
gunzip -t /backups/aibookkeeper/backup.sql.gz && echo "✅ Valid" || echo "❌ Corrupt"
```

---

**Document Version:** 1.0  
**Last Reviewed:** 2024-10-11  
**Next Review:** 2024-11-11

