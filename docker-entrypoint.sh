#!/bin/bash
set -e

echo "Starting AI Bookkeeper services..."

# Start FastAPI backend on port 8000
echo "Starting FastAPI backend on port 8000..."
cd /app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 5

# Start Next.js frontend on port 10000 (Render's exposed port)
echo "Starting Next.js frontend on port 10000..."
cd /app/ai-bookkeeper/frontend
PORT=10000 HOSTNAME=0.0.0.0 NEXT_PUBLIC_API_URL=http://localhost:8000 node server.js &
FRONTEND_PID=$!

echo "Services started:"
echo "  - Backend (FastAPI): http://0.0.0.0:8000"
echo "  - Frontend (Next.js): http://0.0.0.0:10000"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
