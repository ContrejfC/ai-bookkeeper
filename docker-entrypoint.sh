#!/bin/bash
# Startup script for AI Bookkeeper
# This script ensures the backend API is ready before starting the frontend
set -e

echo "🚀 Starting AI Bookkeeper..."

# Use PORT from Cloud Run environment, default to 10000 for local dev
FRONTEND_PORT=${PORT:-10000}
BACKEND_PORT=8000

echo "📋 Configuration:"
echo "   Frontend will listen on: $FRONTEND_PORT"
echo "   Backend will listen on: $BACKEND_PORT"

# Start FastAPI backend
echo "📡 Starting FastAPI backend on port $BACKEND_PORT..."
cd /app
uvicorn app.api.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait for backend to be ready (max 30 seconds)
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:$BACKEND_PORT/ | grep -q "version"; then
    echo "✅ Backend is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ Backend failed to start within 30 seconds"
    exit 1
  fi
  sleep 1
done

# Start Next.js frontend on Cloud Run's PORT
echo "🌐 Starting Next.js frontend on port $FRONTEND_PORT..."
cd /app/frontend
PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!

echo "✅ Both services started successfully"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"

# Wait for both processes
wait -n
EXIT_CODE=$?

echo "⚠️  Service exited with code $EXIT_CODE"
echo "🛑 Shutting down..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
exit $EXIT_CODE