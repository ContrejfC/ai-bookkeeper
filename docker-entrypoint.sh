#!/bin/bash
# Startup script for AI Bookkeeper
# This script ensures the backend API is ready before starting the frontend
set -e

echo "🚀 Starting AI Bookkeeper..."

# Start FastAPI backend
echo "📡 Starting FastAPI backend on port 8000..."
cd /app
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready (max 30 seconds)
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -f http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "✅ Backend is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ Backend failed to start within 30 seconds"
    exit 1
  fi
  sleep 1
done

# Start Next.js frontend
echo "🌐 Starting Next.js frontend on port 10000..."
cd /app/frontend
npm start -- -p 10000 &
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