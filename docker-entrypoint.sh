#!/bin/bash
# Startup script for AI Bookkeeper
set -e

echo "Starting AI Bookkeeper..."

# Start FastAPI backend
echo "Starting FastAPI backend on port 8000..."
cd /app
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &

# Start Next.js frontend
echo "Starting Next.js frontend on port 10000..."
cd /app/frontend
npm start -- -p 10000 &

# Wait for both processes
wait