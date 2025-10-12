#!/bin/bash
# Deployment migration script for staging/production
# Run this after first deploy to set up database and seed data

set -e  # Exit on error

echo "🚀 AI Bookkeeper - Deploy Migration Script"
echo "==========================================="
echo ""

# Check required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

echo "✅ DATABASE_URL configured"
echo ""

# Run Alembic migrations
echo "📦 Running database migrations..."
cd "$(dirname "$0")/.."
python3 -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""

# Seed pilot tenants (optional, only if SEED_ON_DEPLOY=true)
if [ "$SEED_ON_DEPLOY" = "true" ]; then
    echo "🌱 Seeding pilot tenants..."
    python3 scripts/seed_demo_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Pilot tenants seeded"
    else
        echo "⚠️  Seeding failed (non-fatal)"
    fi
else
    echo "ℹ️  Skipping seed (set SEED_ON_DEPLOY=true to enable)"
fi

echo ""

# Health check
echo "🏥 Checking application health..."
sleep 5  # Give app time to start

if command -v curl &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s http://localhost:${PORT:-8000}/healthz || echo "fail")
    
    if [[ $HEALTH_RESPONSE == *"\"status\":\"ok\""* ]]; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check returned unexpected response"
        echo "$HEALTH_RESPONSE"
    fi
else
    echo "ℹ️  curl not available, skipping health check"
fi

echo ""
echo "🎉 Deployment migration complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Verify /healthz and /readyz endpoints"
echo "   2. Check logs for any errors"
echo "   3. Create pilot tenants manually if needed"
echo "   4. Capture screenshots for assessment"

