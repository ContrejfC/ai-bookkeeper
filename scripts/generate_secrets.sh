#!/bin/bash
# Generate secure secrets for production deployment
# Usage: ./scripts/generate_secrets.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    AI Bookkeeper - Production Secrets Generator                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "❌ Error: openssl not found"
    echo "   Install with: brew install openssl (macOS) or apt-get install openssl (Linux)"
    exit 1
fi

echo "Generating secure secrets..."
echo ""

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)
echo "✅ JWT_SECRET (64 chars):"
echo "   JWT_SECRET=$JWT_SECRET"
echo ""

# Generate CSRF secret
CSRF_SECRET=$(openssl rand -hex 32)
echo "✅ CSRF_SECRET (64 chars):"
echo "   CSRF_SECRET=$CSRF_SECRET"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "📋 Copy these to Render Dashboard:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Go to: Dashboard → ai-bookkeeper-api → Environment"
echo ""
echo "Add these two secrets:"
echo ""
echo "JWT_SECRET=$JWT_SECRET"
echo "CSRF_SECRET=$CSRF_SECRET"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  SAVE THESE SECRETS SECURELY!"
echo "   You'll need them if you ever recreate the service."
echo ""
echo "✅ Secrets generated successfully!"
echo ""

