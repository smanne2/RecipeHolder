# Stage 1: Build stage
FROM python:3.13-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies (including libxml2-dev and libxslt-dev for lxml)
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to a virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# Stage 2: Production stage
FROM python:3.13-alpine AS production

# Set working directory
WORKDIR /app

# Install runtime dependencies (including libxml2 and libxslt for lxml)
RUN apk add --no-cache \
    curl \
    libxml2 \
    libxslt

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# Create non-root user for security and data directory
RUN adduser -D -u 1000 recipeuser && \
    mkdir -p /data/recipes && \
    chown -R recipeuser:recipeuser /app /data

# Create entrypoint script to fix permissions on mounted volumes
RUN printf '#!/bin/sh\nchown -R recipeuser:recipeuser /data 2>/dev/null || true\nexec su-exec recipeuser "$@"\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Install su-exec for proper user switching
RUN apk add --no-cache su-exec

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
