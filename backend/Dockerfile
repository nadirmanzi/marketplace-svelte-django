# Stage 1: Build virtual environment
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# Stage 2: Final runtime image
FROM python:3.12-slim as runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies (like netcat for entrypoint and libpq for postgres)
RUN apt-get update && apt-get install -y \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user
RUN addgroup --system django && \
    adduser --system --group django

# Create directories for static, media and logs files
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Copy project files
COPY --chown=django:django . .

# Copy and prepare entrypoint script
COPY --chown=django:django scripts/entrypoint.sh ./scripts/
RUN chmod +x ./scripts/entrypoint.sh

# Run as non-root user
USER django

# Entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
