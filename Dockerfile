# =====================================================
# Stage 1: Builder - Compile Python wheels
# =====================================================
FROM registry.redhat.io/ubi9/python-311:latest AS builder

LABEL maintainer="web-team" \
      description="laforge-foundry - Builder Stage"

# Set working directory
WORKDIR /tmp/build

# Copy requirements
COPY requirements.txt .

# Create wheels from requirements
# Using --no-cache-dir to reduce size
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements.txt

# =====================================================
# Stage 2: Runtime - Minimal production image
# =====================================================
FROM registry.redhat.io/ubi9/python-311:latest

LABEL maintainer="web-team" \
      description="laforge-foundry - Production Runtime" \
      version="1.0.0"

# Set working directory
WORKDIR /app

# Security: Create non-root user (appuser with fixed UID 1001)
# OpenShift SCC compliant
RUN groupadd -r -g 1001 appuser && \
    useradd -r -g appuser -u 1001 -d /app -s /sbin/nologin -c "Application user" appuser && \
    chmod 755 /app

# Copy pre-built wheels from builder stage
COPY --from=builder /tmp/wheels /tmp/wheels

# Install Python dependencies from wheels
RUN pip install --no-cache /tmp/wheels/* && \
    rm -rf /tmp/wheels

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser inventory/ ./inventory/
COPY --chown=appuser:appuser .env.example ./

# Set environment variables
# PYTHONUNBUFFERED: Force stdout/stderr to be unbuffered (see logs immediately)
# PYTHONDONTWRITEBYTECODE: Don't write .pyc files (reduce image footprint)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    PORT=8080 \
    HOST=0.0.0.0

# Expose port 8080 (OpenShift service port)
EXPOSE 8080

# Health check for Docker runtime (not used by K8s, but useful for local testing)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Switch to non-root user
USER appuser

# Entrypoint: Run FastAPI application with uvicorn
# --access-log: Disabled to reduce noise, rely on application logging
# --use-colors: Disabled in container (logs are captured anyway)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--access-log"]