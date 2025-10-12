#!/bin/bash
#
# Setup Analytics Rollup Cron Job (Phase 2b)
#
# Schedules daily analytics rollup at 02:00 local time
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setting up Analytics Rollup Cron Job"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Detect Python interpreter
if command -v python3 &> /dev/null; then
    PYTHON_BIN="$(which python3)"
elif command -v python &> /dev/null; then
    PYTHON_BIN="$(which python)"
else
    echo "❌ Error: Python not found"
    exit 1
fi

echo "Python: $PYTHON_BIN"
echo "Project: $PROJECT_ROOT"

# Create cron job entry
CRON_ENTRY="0 2 * * * cd $PROJECT_ROOT && $PYTHON_BIN jobs/analytics_rollup.py >> logs/analytics_cron.log 2>&1"

echo ""
echo "Cron entry to add:"
echo "$CRON_ENTRY"
echo ""

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -F "analytics_rollup.py" >/dev/null; then
    echo "⚠️  Cron job already exists. Skipping."
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep analytics_rollup.py || true
else
    # Add to crontab
    echo "Adding to crontab..."
    
    # Save current crontab
    crontab -l > /tmp/crontab.bak 2>/dev/null || touch /tmp/crontab.bak
    
    # Add new entry
    echo "$CRON_ENTRY" >> /tmp/crontab.bak
    
    # Install new crontab
    crontab /tmp/crontab.bak
    
    echo "✅ Cron job installed successfully"
fi

echo ""
echo "To verify:"
echo "  crontab -l | grep analytics"
echo ""
echo "To test manually:"
echo "  cd $PROJECT_ROOT"
echo "  $PYTHON_BIN jobs/analytics_rollup.py"
echo ""
echo "Logs will be written to:"
echo "  $PROJECT_ROOT/logs/analytics_cron.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Analytics Cron Setup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

