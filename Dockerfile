# AI Bookkeeper - Production Dockerfile for Render
# Tesseract OCR + Python 3.11-slim

FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p logs/analytics reports/analytics artifacts/receipts data && \
    chmod -R 755 logs reports artifacts data

# Health check (Render uses port 10000)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS http://localhost:10000/healthz || exit 1

# Default command (Render will override via startCommand)
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "10000"]
