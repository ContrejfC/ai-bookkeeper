#!/bin/bash
#===============================================================================
# AI Bookkeeper - Docker Container Startup Script
#===============================================================================
#
# Purpose:
#   Orchestrates the startup of both FastAPI backend and Next.js frontend
#   services in a single container for Google Cloud Run deployment.
#
# Flow:
#   1. Start FastAPI backend on port 8000 (internal)
#   2. Wait for backend health check (max 120 seconds)
#   3. Start Next.js frontend on Cloud Run's $PORT (exposed)
#   4. Monitor both services and exit if either fails
#
# Environment Variables:
#   - PORT: Cloud Run provides this (defaults to 10000 locally)
#   - BACKEND_PORT: Fixed at 8000 (internal only)
#
# Exit Codes:
#   - 0: Both services running successfully
#   - 1: Backend failed to start within timeout
#   - Other: Service crashed
#
#===============================================================================

# Exit immediately if any command fails
set -e

echo "🚀 Starting AI Bookkeeper..."

# Port Configuration
# Cloud Run sets $PORT dynamically, use 10000 for local development
FRONTEND_PORT=${PORT:-10000}
BACKEND_PORT=8000

echo "📋 Configuration:"
echo "   Frontend will listen on: $FRONTEND_PORT"
echo "   Backend will listen on: $BACKEND_PORT"

#===============================================================================
# Step 1: Start FastAPI Backend
#===============================================================================
# The backend MUST start first because the frontend will proxy API calls to it.
# Run in background (&) to allow health checking while it initializes.
echo "📡 Starting FastAPI backend on port $BACKEND_PORT..."
cd /app
uvicorn app.api.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

#===============================================================================
# Step 2: Health Check - Wait for Backend Readiness
#===============================================================================
# Cloud Run requires services to respond within timeout (default 300s).
# We poll the root endpoint which returns JSON with "version" field.
# If backend doesn't respond in 120 seconds, fail fast to avoid Cloud Run timeout.
echo "⏳ Waiting for backend to be ready..."
for i in {1..120}; do
  # Check if backend is responding with valid JSON
  if curl -s http://localhost:$BACKEND_PORT/ | grep -q "version"; then
    echo "✅ Backend is ready!"
    break
  fi
  
  # After 120 seconds, exit with error
  if [ $i -eq 120 ]; then
    echo "❌ Backend failed to start within 120 seconds"
    echo "   This usually indicates:"
    echo "   - Database connection failure"
    echo "   - Import error in Python code"
    echo "   - Missing environment variables"
    exit 1
  fi
  
  sleep 1
done

#===============================================================================
# Step 3: Start Next.js Frontend
#===============================================================================
# Frontend starts AFTER backend is healthy.
# Frontend proxies /api/* requests to backend on port 8000.
# Cloud Run routes external traffic to this frontend port.
echo "🌐 Starting Next.js frontend on port $FRONTEND_PORT..."
cd /app/frontend
PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!

echo "✅ Both services started successfully"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"

#===============================================================================
# Step 4: Monitor Services
#===============================================================================
# Wait for any process to exit (wait -n).
# If either service crashes, shut down the container gracefully.
# Cloud Run will restart the container automatically.
wait -n
EXIT_CODE=$?

echo "⚠️  Service exited with code $EXIT_CODE"
echo "🛑 Shutting down..."

# Kill both processes (ignore errors if already dead)
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true

exit $EXIT_CODE