#===============================================================================
# AI Bookkeeper - Multi-Stage Docker Container
#===============================================================================
#
# This Dockerfile builds a production-ready container that runs both the
# FastAPI backend and Next.js frontend in a single container.
#
# Architecture:
# ------------
# Stage 1: Build Next.js frontend (node:20-alpine)
# Stage 2: Run Python backend + serve built frontend (python:3.11-slim)
#
# Why Multi-Stage?
# ----------------
# - Smaller final image (no Node.js in production)
# - Faster builds (caches npm dependencies)
# - Better security (fewer attack surfaces)
# - Separates build-time vs runtime dependencies
#
# Services Running:
# ----------------
# 1. FastAPI Backend (Uvicorn) on port 8000
#    - Serves API endpoints (/api/*)
#    - Health checks (/healthz, /readyz)
#    - API documentation (/docs)
#
# 2. Next.js Frontend on port 10000
#    - Serves UI pages (/, /dashboard, /pricing)
#    - Proxies API calls to backend
#    - Static assets and React app
#
# Deployment:
# ----------
# Render exposes port 10000 (frontend) to the internet.
# Frontend proxies /api/* requests to backend on port 8000 (internal).
#
#===============================================================================

# ============================================================================
# STAGE 1: Build Next.js Frontend
# ============================================================================
# Uses Node.js Alpine for minimal image size during build
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy package files first (enables Docker layer caching)
# If package.json doesn't change, npm install is cached
COPY frontend/package*.json ./

# Install ONLY production dependencies (skip devDependencies)
# --ci uses package-lock.json for reproducible builds
RUN npm ci --only=production

# Copy all frontend source code
COPY frontend/ ./

# Build Next.js for production
# Creates optimized static bundle in .next/
RUN npm run build

# ============================================================================
# STAGE 2: Production Runtime Container
# ============================================================================
# Python slim image (Debian-based, includes system libraries)
FROM python:3.11-slim

# ----------------------------------------------------------------------------
# Install System Dependencies
# ----------------------------------------------------------------------------
# tesseract-ocr: OCR engine for receipt text extraction
# tesseract-ocr-eng: English language data for OCR
# libtesseract-dev: Development libraries for Python pytesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Clean up apt cache to reduce image size

# Set working directory for application
WORKDIR /app

# ----------------------------------------------------------------------------
# Install Python Dependencies
# ----------------------------------------------------------------------------
# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python packages
# --no-cache-dir: Don't cache pip downloads (saves space)
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------------
# Copy Backend Application Code
# ----------------------------------------------------------------------------
COPY app/ ./app/              # FastAPI application
COPY alembic/ ./alembic/      # Database migrations
COPY alembic.ini ./           # Alembic configuration
COPY scripts/ ./scripts/      # Utility scripts
COPY main.py ./               # Entry point

# ----------------------------------------------------------------------------
# Copy Built Frontend from Stage 1
# ----------------------------------------------------------------------------
# Only copy the production build, not source code
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# ----------------------------------------------------------------------------
# Create Startup Script
# ----------------------------------------------------------------------------
# This script starts both services in the background and waits for both
#
# Service 1: FastAPI Backend (Uvicorn)
#   - Listens on 0.0.0.0:8000 (internal)
#   - Auto-reloads on code changes (dev) or runs stable (prod)
#
# Service 2: Next.js Frontend
#   - Listens on 0.0.0.0:10000 (exposed to internet)
#   - Serves static pages and proxies API calls
#
# The 'wait' command keeps container running until both services exit
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting AI Bookkeeper services..."\n\
\n\
# Start backend API\n\
echo "→ Starting FastAPI backend on port 8000..."\n\
cd /app\n\
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &\n\
BACKEND_PID=$!\n\
\n\
# Start frontend\n\
echo "→ Starting Next.js frontend on port 10000..."\n\
cd /app/frontend\n\
npm start -- -p 10000 &\n\
FRONTEND_PID=$!\n\
\n\
echo "✓ Services started"\n\
echo "  Backend PID: $BACKEND_PID"\n\
echo "  Frontend PID: $FRONTEND_PID"\n\
\n\
# Wait for both services (exit if either crashes)\n\
wait -n\n\
EXIT_CODE=$?\n\
\n\
echo "⚠ Service exited with code $EXIT_CODE"\n\
echo "Shutting down..."\n\
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null\n\
exit $EXIT_CODE\n\
' > /app/start.sh && chmod +x /app/start.sh

# ----------------------------------------------------------------------------
# Expose Ports
# ----------------------------------------------------------------------------
# Port 8000: Backend API (internal, not exposed to internet)
# Port 10000: Frontend UI (exposed to internet via Render/Cloud Run)
EXPOSE 8000 10000

# ----------------------------------------------------------------------------
# Health Check Configuration
# ----------------------------------------------------------------------------
# Kubernetes and cloud platforms use this to monitor container health
#
# --interval=30s: Check every 30 seconds
# --timeout=3s: Fail if check takes longer than 3 seconds
# --start-period=5s: Wait 5 seconds before first check (startup time)
# --retries=3: Mark unhealthy after 3 consecutive failures
#
# The check hits /healthz endpoint on backend API
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# ----------------------------------------------------------------------------
# Container Entry Point
# ----------------------------------------------------------------------------
# Run the startup script that launches both services
CMD ["/app/start.sh"]

#===============================================================================
# Building and Running:
#===============================================================================
#
# Build:
#   docker build -t ai-bookkeeper .
#
# Run locally:
#   docker run -p 8000:8000 -p 10000:10000 \
#     -e DATABASE_URL=postgresql://... \
#     -e JWT_SECRET=your-secret \
#     ai-bookkeeper
#
# Deploy to Google Cloud Run:
#   gcloud builds submit --tag gcr.io/PROJECT_ID/ai-bookkeeper
#   gcloud run deploy --image gcr.io/PROJECT_ID/ai-bookkeeper --port 10000
#
# Deploy to Render:
#   Push to GitHub, Render auto-builds from this Dockerfile
#
#===============================================================================