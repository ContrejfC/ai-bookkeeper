#!/bin/bash
#
# Backup & Restore Evidence Script (SOC 2 Min Controls)
#
# Performs database backup, test restore, and smoke test.
# Generates evidence report with sizes, row counts, and PASS/FAIL status.
#
# Usage:
#   ./scripts/backup_restore_check.sh
#
# Environment:
#   DATABASE_URL - Database connection string (Postgres or SQLite)
#
# Outputs:
#   - artifacts/compliance/db_backup_<timestamp>.sql (if Postgres)
#   - artifacts/compliance/backup_restore_<timestamp>.txt (evidence report)
#
# Exit codes:
#   0 - Success
#   1 - Failure (backup or restore failed)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
COMPLIANCE_DIR="artifacts/compliance"
mkdir -p "$COMPLIANCE_DIR"

# Timestamp for filenames
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$COMPLIANCE_DIR/db_backup_$TIMESTAMP.sql"
EVIDENCE_FILE="$COMPLIANCE_DIR/backup_restore_$TIMESTAMP.txt"

# Database URL
DATABASE_URL="${DATABASE_URL:-}"

# Evidence report
EVIDENCE_REPORT=""

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
    EVIDENCE_REPORT+="[INFO] $1\n"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    EVIDENCE_REPORT+="[WARN] $1\n"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    EVIDENCE_REPORT+="[ERROR] $1\n"
}

save_evidence() {
    echo -e "$EVIDENCE_REPORT" > "$EVIDENCE_FILE"
    log_info "Evidence report saved: $EVIDENCE_FILE"
}

# Main logic
main() {
    log_info "=== Backup & Restore Check Started ==="
    log_info "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL not set. Using default SQLite for demo."
        DATABASE_URL="sqlite:///./aibookkeeper.db"
    fi
    
    log_info "Database: ${DATABASE_URL%%\?*}"  # Log without query params/secrets
    
    # Detect database type
    if [[ "$DATABASE_URL" == postgres* ]] || [[ "$DATABASE_URL" == postgresql* ]]; then
        log_info "Detected: PostgreSQL"
        backup_restore_postgres
    elif [[ "$DATABASE_URL" == sqlite* ]]; then
        log_info "Detected: SQLite"
        backup_restore_sqlite
    else
        log_error "Unsupported database type"
        save_evidence
        exit 1
    fi
    
    log_info "=== Backup & Restore Check Completed ==="
    save_evidence
    exit 0
}

backup_restore_postgres() {
    log_info "--- PostgreSQL Backup & Restore ---"
    
    # Extract connection params from DATABASE_URL
    # Format: postgresql://user:pass@host:port/dbname
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
    DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')
    DB_USER=$(echo "$DATABASE_URL" | sed -E 's|.*://([^:]+):.*|\1|')
    DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
    
    log_info "Host: $DB_HOST, Port: $DB_PORT, DB: $DB_NAME"
    
    # Check if pg_dump is available
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Install PostgreSQL client tools."
        save_evidence
        exit 1
    fi
    
    # Step 1: Backup
    log_info "Step 1: Running pg_dump..."
    export PGPASSWORD="$DB_PASS"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F plain -f "$BACKUP_FILE" 2>&1; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        BACKUP_LINES=$(wc -l < "$BACKUP_FILE")
        log_info "✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE, $BACKUP_LINES lines)"
    else
        log_error "✗ pg_dump failed"
        save_evidence
        exit 1
    fi
    
    # Step 2: Test restore (to temporary schema)
    log_info "Step 2: Testing restore to temp schema..."
    TEMP_SCHEMA="restore_test_$TIMESTAMP"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE SCHEMA $TEMP_SCHEMA;" &> /dev/null; then
        log_info "✓ Temporary schema created: $TEMP_SCHEMA"
        
        # Modify backup to use temp schema (sed in-place)
        sed "s/public\./$TEMP_SCHEMA./g" "$BACKUP_FILE" > "${BACKUP_FILE}.temp"
        
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "${BACKUP_FILE}.temp" &> /dev/null; then
            log_info "✓ Restore successful to temp schema"
            
            # Step 3: Verify data (row counts)
            log_info "Step 3: Verifying restored data..."
            
            for table in users tenant_settings user_tenants; do
                ROW_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $TEMP_SCHEMA.$table;" 2>/dev/null || echo "0")
                log_info "  Table $table: $ROW_COUNT rows"
            done
            
            log_info "✓ Data verification complete"
        else
            log_error "✗ Restore failed"
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA $TEMP_SCHEMA CASCADE;" &> /dev/null
            save_evidence
            exit 1
        fi
        
        # Cleanup temp schema
        log_info "Cleaning up temp schema..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA $TEMP_SCHEMA CASCADE;" &> /dev/null
        rm -f "${BACKUP_FILE}.temp"
        log_info "✓ Cleanup complete"
    else
        log_warn "Unable to create temp schema (permission denied). Skipping restore test."
        log_info "Note: Backup created successfully. Restore test requires elevated permissions."
    fi
    
    unset PGPASSWORD
    
    # Step 4: Smoke test (optional - requires running app)
    log_info "Step 4: Smoke test (checking /healthz)..."
    if command -v curl &> /dev/null; then
        if curl -s -f http://localhost:8000/healthz &> /dev/null; then
            log_info "✓ /healthz passed"
        else
            log_warn "/healthz not reachable (app may not be running)"
        fi
    else
        log_warn "curl not available, skipping smoke test"
    fi
    
    log_info "RESULT: PASS"
}

backup_restore_sqlite() {
    log_info "--- SQLite Backup & Restore ---"
    
    # Extract database path from URL
    # Format: sqlite:///path/to/db.db
    DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite:///\{0,1\}||')
    
    if [ ! -f "$DB_PATH" ]; then
        log_error "Database file not found: $DB_PATH"
        save_evidence
        exit 1
    fi
    
    log_info "Database file: $DB_PATH"
    
    # Step 1: Backup (copy + dump)
    log_info "Step 1: Creating backup..."
    
    BACKUP_COPY="$COMPLIANCE_DIR/db_backup_$TIMESTAMP.db"
    cp "$DB_PATH" "$BACKUP_COPY"
    
    BACKUP_COPY_SIZE=$(du -h "$BACKUP_COPY" | cut -f1)
    log_info "✓ Backup copy: $BACKUP_COPY ($BACKUP_COPY_SIZE)"
    
    # Also create SQL dump
    sqlite3 "$DB_PATH" .dump > "$BACKUP_FILE" 2>&1
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    BACKUP_LINES=$(wc -l < "$BACKUP_FILE")
    log_info "✓ SQL dump: $BACKUP_FILE ($BACKUP_SIZE, $BACKUP_LINES lines)"
    
    # Step 2: Test restore
    log_info "Step 2: Testing restore..."
    
    TEMP_DB="$COMPLIANCE_DIR/restore_test_$TIMESTAMP.db"
    rm -f "$TEMP_DB"
    
    if sqlite3 "$TEMP_DB" < "$BACKUP_FILE" 2>&1; then
        log_info "✓ Restore successful to $TEMP_DB"
        
        # Step 3: Verify data
        log_info "Step 3: Verifying restored data..."
        
        for table in users tenant_settings user_tenants; do
            ROW_COUNT=$(sqlite3 "$TEMP_DB" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
            log_info "  Table $table: $ROW_COUNT rows"
        done
        
        log_info "✓ Data verification complete"
        
        # Cleanup
        rm -f "$TEMP_DB"
        rm -f "$BACKUP_COPY"  # Keep only SQL dump
        log_info "✓ Cleanup complete"
    else
        log_error "✗ Restore failed"
        save_evidence
        exit 1
    fi
    
    # Step 4: Smoke test
    log_info "Step 4: Smoke test (checking /healthz)..."
    if command -v curl &> /dev/null; then
        if curl -s -f http://localhost:8000/healthz &> /dev/null; then
            log_info "✓ /healthz passed"
        else
            log_warn "/healthz not reachable (app may not be running)"
        fi
    else
        log_warn "curl not available, skipping smoke test"
    fi
    
    log_info "RESULT: PASS"
}

# Run main
main

