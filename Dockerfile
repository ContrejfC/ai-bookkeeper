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

# Install ALL dependencies (including devDependencies needed for build)
# Using npm install instead of npm ci for better compatibility in Cloud Build
RUN npm install --legacy-peer-deps

# Copy all frontend source code
COPY frontend/ ./

# Build Next.js for production
# Creates optimized static bundle in .next/
RUN npm run build

# Remove devDependencies after build to reduce image size
RUN npm prune --production --legacy-peer-deps

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
# FastAPI application
COPY app/ ./app/
# Configuration files
COPY config/ ./config/
# Database migrations
COPY alembic/ ./alembic/
# Alembic configuration
COPY alembic.ini ./
# Utility scripts
COPY scripts/ ./scripts/
# Entry point
COPY main.py ./

# ----------------------------------------------------------------------------
# Copy Built Frontend from Stage 1
# ----------------------------------------------------------------------------
# Only copy the production build, not source code
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# ----------------------------------------------------------------------------
# Copy Startup Script
# ----------------------------------------------------------------------------
# This script starts both services in the background and waits for both
#
# Service 1: FastAPI Backend (Uvicorn)
#   - Listens on 0.0.0.0:8000 (internal)
#   - Waits for backend to be healthy before starting frontend
#
# Service 2: Next.js Frontend
#   - Listens on 0.0.0.0:10000 (exposed to internet)
#   - Serves static pages and proxies API calls to backend
#
# The startup script ensures proper initialization order and health checking
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# ----------------------------------------------------------------------------
# Expose Ports
# ----------------------------------------------------------------------------
# Port 8000: Backend API (internal, not exposed to internet)
# Port 8080/10000: Frontend UI (uses $PORT from Cloud Run, defaults to 10000 locally)
# Cloud Run will route traffic to whatever port is set in $PORT environment variable
EXPOSE 8000 8080 10000

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
CMD ["/app/docker-entrypoint.sh"]

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