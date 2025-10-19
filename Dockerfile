# AI Bookkeeper - Production Dockerfile for Render
# Multi-stage build: Node.js for frontend + Python for backend

# ============================================================================
# Stage 1: Build Next.js Frontend
# ============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY package*.json ./

# Install dependencies (devDependencies needed for build). Use npm install
# because this repo does not include a package-lock.json, which would break npm ci.
RUN npm install

# Copy frontend source code
COPY . ./

# Build Next.js app for production
RUN npm run build

# ============================================================================
# Stage 2: Python Backend with Frontend Static Files
# ============================================================================
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NEXT_PUBLIC_API_URL=http://localhost:8000

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    ghostscript \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    build-essential \
    libpq-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Copy built Next.js frontend from Stage 1 (standalone mode)
COPY --from=frontend-builder /frontend/.next/standalone /app/
COPY --from=frontend-builder /frontend/.next/static /app/.next/static
COPY --from=frontend-builder /frontend/public /app/public
COPY --from=frontend-builder /frontend/package.json /app/package.json

# Create necessary directories
RUN mkdir -p logs/analytics reports/analytics artifacts/receipts data && \
    chmod -R 755 logs reports artifacts data frontend

# Health check (Render uses port 10000)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://localhost:10000/healthz || exit 1

# We'll use a startup script to run both backend and frontend
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Default command (Render will override via startCommand)
CMD ["/app/docker-entrypoint.sh"]
