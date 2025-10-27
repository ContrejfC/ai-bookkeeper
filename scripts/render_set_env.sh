#!/usr/bin/env bash
set -euo pipefail

# Script to set environment variable on Render service and trigger deploy
# Usage: RENDER_API_KEY=xxx ./scripts/render_set_env.sh <service_name> <env_key> <env_value>

RENDER_API_KEY="${RENDER_API_KEY:?RENDER_API_KEY required}"
SERVICE_NAME="${1:?Service name required}"
ENV_KEY="${2:?Environment key required}"
ENV_VALUE="${3:?Environment value required}"

BASE_URL="https://api.render.com/v1"

echo "🔍 Finding service: $SERVICE_NAME"

# Get all services
SERVICES=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "$BASE_URL/services" | jq -r '.')

# Find service by name
SERVICE_ID=$(echo "$SERVICES" | jq -r --arg name "$SERVICE_NAME" \
  '.[] | select(.service.name == $name) | .service.id')

if [ -z "$SERVICE_ID" ] || [ "$SERVICE_ID" = "null" ]; then
    echo "❌ Service '$SERVICE_NAME' not found"
    echo ""
    echo "Available services:"
    echo "$SERVICES" | jq -r '.[] | .service | "\(.name) (\(.id))"'
    exit 1
fi

echo "✅ Found service ID: $SERVICE_ID"
echo ""

# Get current env vars
echo "📋 Current environment variables:"
CURRENT_ENV=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "$BASE_URL/services/$SERVICE_ID/env-vars")

echo "$CURRENT_ENV" | jq -r '.[] | "\(.key) = \(.value)"' | head -10

# Check if env var exists
ENV_VAR_ID=$(echo "$CURRENT_ENV" | jq -r --arg key "$ENV_KEY" \
  '.[] | select(.key == $key) | .id')

if [ -n "$ENV_VAR_ID" ] && [ "$ENV_VAR_ID" != "null" ]; then
    echo ""
    echo "🔄 Updating existing env var: $ENV_KEY"
    
    curl -s -X PATCH \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      "$BASE_URL/services/$SERVICE_ID/env-vars/$ENV_VAR_ID" \
      -d "{\"value\": \"$ENV_VALUE\"}" | jq '.'
else
    echo ""
    echo "➕ Creating new env var: $ENV_KEY"
    
    curl -s -X POST \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      "$BASE_URL/services/$SERVICE_ID/env-vars" \
      -d "{\"key\": \"$ENV_KEY\", \"value\": \"$ENV_VALUE\"}" | jq '.'
fi

echo ""
echo "🚀 Triggering deploy..."

# Trigger deploy
DEPLOY=$(curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/services/$SERVICE_ID/deploys" \
  -d '{"clearCache": false}')

DEPLOY_ID=$(echo "$DEPLOY" | jq -r '.id')

echo "✅ Deploy triggered: $DEPLOY_ID"
echo ""
echo "📊 Deploy status:"
echo "$DEPLOY" | jq '{id: .id, status: .status, createdAt: .createdAt}'

echo ""
echo "🔗 Monitor deploy at:"
echo "https://dashboard.render.com/services/$SERVICE_ID/deploys/$DEPLOY_ID"

# Get service URL
SERVICE_URL=$(echo "$SERVICES" | jq -r --arg id "$SERVICE_ID" \
  '.[] | select(.service.id == $id) | .service.serviceDetails.url')

echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "$SERVICE_URL" > tmp/WEB_URL.txt
echo "✅ Saved to tmp/WEB_URL.txt"

