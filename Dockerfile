# ==============================================================================
# Multi-Stage Dockerfile for XLA_TGMT Image Processing Benchmark System
# Base Image: Python 3.11-slim
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder (Compile dependencies and create pre-built wheels)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for C-extension packages (Pillow, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade packaging tools and build wheels for all requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ------------------------------------------------------------------------------
# Stage 2: Runtime (Minimal production container)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Python execution optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

# Install essential runtime shared libraries:
# - libgl1: OpenGL library required by OpenCV / graphical rendering
# - libglib2.0-0: Core application building blocks for image processing
# - libmagic1: System magic bytes file type identification library
# - curl: Lightweight HTTP probe for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built Python packages from builder stage (zero compiler baggage)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Create dedicated non-root user & group (Security Hardening: UID/GID 1000)
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

# Pre-create data directories with write permissions for appuser
RUN mkdir -p /app/uploads /app/outputs /app/data/sample_images \
    && chown -R appuser:appgroup /app

# Copy application code into container
COPY --chown=appuser:appgroup . /app

# Run as non-root user
USER appuser

# Expose Web port
EXPOSE 5000

# Docker Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production WSGI Server entrypoint (Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--timeout", "120", "run:app"]

