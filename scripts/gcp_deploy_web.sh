#!/usr/bin/env bash
set -euo pipefail
: "${PROJECT:?}"; : "${REGION:?}"
REPO="app"
WEB_IMG="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/web:latest"
API_URL=$(cat tmp/API_URL.txt)
gcloud builds submit ./frontend --tag "$WEB_IMG"
gcloud run deploy ai-bookkeeper-web --image "$WEB_IMG" --region "$REGION" --allow-unauthenticated --port 3000 --min-instances 1 --max-instances 10 --cpu 1 --memory 512Mi --set-env-vars "NEXT_PUBLIC_API_URL=${API_URL}"
WEB_URL=$(gcloud run services describe ai-bookkeeper-web --region "$REGION" --format='value(status.url)')
mkdir -p tmp && echo "$WEB_URL" > tmp/WEB_URL.txt && echo "WEB_URL=$WEB_URL"

