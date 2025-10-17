#!/usr/bin/env bash
#
# Alembic Baseline Repair Script
#
# Usage:
#   # For existing production DB with tables already present:
#   ALREADY_DEPLOYED=true ./scripts/db_repair_baseline.sh
#
#   # For clean/new database:
#   ./scripts/db_repair_baseline.sh
#

set -e

echo "========================================"
echo "  Alembic Baseline Repair"
echo "========================================"
echo ""

# Check if this is an existing deployment
if [ "${ALREADY_DEPLOYED:-false}" = "true" ]; then
    echo "Mode: EXISTING DEPLOYMENT"
    echo "Will stamp baseline then upgrade..."
    echo ""
    
    # Stamp the baseline revision
    echo "→ Stamping revision 001 (baseline)..."
    alembic stamp 001
    
    # Then upgrade to head
    echo "→ Upgrading to head..."
    alembic upgrade head
    
    echo ""
    echo "✓ Existing database repaired and upgraded"
else
    echo "Mode: CLEAN DATABASE"
    echo "Will run normal upgrade..."
    echo ""
    
    # Normal upgrade path
    alembic upgrade head
    
    echo ""
    echo "✓ Clean database migrated to head"
fi

echo ""
echo "→ Verifying single head..."
HEAD_COUNT=$(alembic heads 2>/dev/null | wc -l | tr -d ' ')

if [ "$HEAD_COUNT" -eq 1 ]; then
    echo "✓ Single head confirmed"
    alembic current
else
    echo "⚠ WARNING: Multiple heads detected ($HEAD_COUNT)"
    alembic heads
    exit 1
fi

echo ""
echo "========================================"
echo "  Repair Complete"
echo "========================================"

