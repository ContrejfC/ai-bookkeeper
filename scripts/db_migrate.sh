#!/bin/bash
# Database migration script with single-head validation
#
# Usage:
#   ./scripts/db_migrate.sh
#
# Environment:
#   ALLOW_STAMP=true  # Allow stamping head before upgrade (default: false)
#
# Behavior:
#   - On cold DB: alembic upgrade head
#   - On existing DB: check for drift, optionally stamp, then upgrade
#   - Fails if multiple Alembic heads detected

set -e

echo "=== AI Bookkeeper - Database Migration ==="

# Check for multiple heads
echo "Checking for multiple Alembic heads..."
HEAD_COUNT=$(alembic heads 2>/dev/null | grep -v "^INFO" | grep -c "^" || echo "0")

if [ "$HEAD_COUNT" -gt 1 ]; then
    echo "❌ ERROR: Multiple Alembic heads detected ($HEAD_COUNT heads)"
    echo "   This indicates a branched migration history."
    echo "   Fix by merging branches or resolving conflicts."
    alembic heads
    exit 1
elif [ "$HEAD_COUNT" -eq 0 ]; then
    echo "⚠️  WARNING: No Alembic heads found"
    echo "   This may indicate no migrations exist or Alembic not initialized."
fi

echo "✓ Single Alembic head confirmed"

# Check current database state
echo ""
echo "Checking current database state..."
CURRENT=$(alembic current 2>&1 || echo "none")

if echo "$CURRENT" | grep -q "none" || echo "$CURRENT" | grep -qi "error"; then
    echo "Cold database detected (no version table or error)"
    echo "Running: alembic upgrade head"
    alembic upgrade head
    echo "✓ Migration completed"
else
    echo "Existing database detected"
    echo "Current revision: $CURRENT"
    
    # Check for drift
    if echo "$CURRENT" | grep -qi "head"; then
        echo "✓ Database is at head, no migration needed"
    else
        # Check if stamping is allowed
        ALLOW_STAMP=${ALLOW_STAMP:-false}
        
        if [ "$ALLOW_STAMP" = "true" ]; then
            echo "Stamping head (ALLOW_STAMP=true)..."
            alembic stamp head
        fi
        
        echo "Running: alembic upgrade head"
        alembic upgrade head
        echo "✓ Migration completed"
    fi
fi

echo ""
echo "=== Migration Complete ==="
echo "Final state:"
alembic current

