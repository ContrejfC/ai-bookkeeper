# AI Bookkeeper - Production Dockerfile for Render
# Multi-stage build: Node.js for frontend + Python for backend

# ============================================================================
# Stage 1: Build Next.js Frontend
# ============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ============================================================================
# Stage 2: Python Backend with Frontend Static Files
# ============================================================================
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

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

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built Next.js frontend from Stage 1 (standalone output)
COPY --from=frontend-builder /build/.next/standalone /app/
COPY --from=frontend-builder /build/.next/static /app/ai-bookkeeper/frontend/.next/static
COPY --from=frontend-builder /build/public /app/ai-bookkeeper/frontend/public

# Create necessary directories
RUN mkdir -p logs/analytics reports/analytics artifacts/receipts data && \
    chmod -R 755 logs reports artifacts data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://localhost:10000/ || exit 1

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 10000

# Start services
CMD ["/app/docker-entrypoint.sh"]
