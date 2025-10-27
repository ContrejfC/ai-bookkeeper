FROM python:3.11-slim
WORKDIR /app

# Install CA certificates and PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY . .

# Set environment
ENV PYTHONPATH=/app
EXPOSE 8080

# Use $PORT environment variable (Cloud Run sets this)
CMD ["sh", "-c", "uvicorn api.main_minimal:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --timeout-keep-alive 65"]
