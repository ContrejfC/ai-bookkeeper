#!/bin/bash
# Docker entrypoint script to run both backend and frontend

set -e

echo "Starting AI Bookkeeper services..."

# Start FastAPI backend on port 8000
cd /app
echo "Starting FastAPI backend on port 8000..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --proxy-headers &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 5

# Start Next.js frontend on port 10000 (Render's exposed port)
echo "Starting Next.js frontend on port 10000..."
PORT=10000 HOSTNAME=0.0.0.0 node server.js &
FRONTEND_PID=$!

echo "Services started:"
echo "  - Backend (FastAPI): http://0.0.0.0:8000"
echo "  - Frontend (Next.js): http://0.0.0.0:10000"

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID $BACKEND_PID 2>/dev/null || true
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Wait for both processes; only exit when both have exited
wait $FRONTEND_PID
FRONTEND_CODE=$?
wait $BACKEND_PID
BACKEND_CODE=$?

echo "Frontend exited with code $FRONTEND_CODE, Backend exited with code $BACKEND_CODE"
shutdown

