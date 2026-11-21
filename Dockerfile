# ==============================================================================
# KubePulse SRE Platform - Production Multi-Stage Dockerfile
# ==============================================================================

# Stage 1: Build stage with compiler dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image with non-root security context
FROM python:3.11-slim AS runner

WORKDIR /app

# Create unprivileged SRE user
RUN groupadd -g 10001 sre && \
    useradd -u 10001 -g sre -s /bin/bash -m sre

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/sre/.local
ENV PATH=/home/sre/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV KUBEPULSE_PORT=5050

# Copy application source code
COPY --chown=sre:sre . /app

# Switch to unprivileged user
USER sre

EXPOSE 5050

# Native health check against Kubernetes healthz probe
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5050/healthz')" || exit 1

CMD ["python", "run.py"]
