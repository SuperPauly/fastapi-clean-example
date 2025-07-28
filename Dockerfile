# Multi-stage build for FastAPI Clean Architecture Template
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hatch
RUN pip install hatch

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./
COPY LICENSE ./

# Create hatch environment and install dependencies
RUN hatch env create default

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy from builder stage
COPY --from=builder /app /app
COPY --from=builder /root/.local/share/hatch /root/.local/share/hatch

# Install Hatch in production stage
RUN pip install hatch

# Copy additional files
COPY settings.toml ./
COPY manage_config.py ./
COPY loguru_config_tui.py ./

# Create necessary directories
RUN mkdir -p logs configs static templates && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["hatch", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

