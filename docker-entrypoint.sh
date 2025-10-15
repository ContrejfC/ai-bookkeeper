#!/bin/bash
# Docker entrypoint script to run both backend and frontend

set -e

echo "Starting AI Bookkeeper services..."

# Start FastAPI backend on port 8000
cd /app
echo "Starting FastAPI backend on port 8000..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 5

# Start Next.js frontend on port 10000 (Render's exposed port)
cd /app/frontend
echo "Starting Next.js frontend on port 10000..."
PORT=10000 HOSTNAME=0.0.0.0 npm start &
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

# Wait for both processes - exit if either crashes
wait -n $FRONTEND_PID $BACKEND_PID
EXIT_CODE=$?

echo "One of the services exited with code $EXIT_CODE"
shutdown

