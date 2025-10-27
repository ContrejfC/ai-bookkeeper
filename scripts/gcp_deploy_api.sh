#!/usr/bin/env bash
set -euo pipefail
: "${PROJECT:?}"; : "${REGION:?}"
REPO="app"
API_IMG="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/api:latest"
gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" || true
gcloud builds submit ./app --tag "$API_IMG"
ARGS=(--image "$API_IMG" --region "$REGION" --allow-unauthenticated --port 8080 --min-instances 1 --max-instances 10 --cpu 1 --memory 512Mi --set-env-vars "ALLOWED_ORIGINS=${WEB_ORIGINS}")
if [[ -n "${DB_URL:-}" ]]; then ARGS+=(--set-env-vars "DATABASE_URL=${DB_URL}"); fi
gcloud run deploy ai-bookkeeper-api "${ARGS[@]}"
API_URL=$(gcloud run services describe ai-bookkeeper-api --region "$REGION" --format='value(status.url)')
mkdir -p tmp && echo "$API_URL" > tmp/API_URL.txt && echo "API_URL=$API_URL"

