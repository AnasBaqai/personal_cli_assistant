# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build pip wheel

# Copy project files for building
COPY pyproject.toml .
COPY src/ ./src/

# Build wheel
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# -------------------------------------------
# Runtime stage
# -------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY src/ ./src/

# Set environment for Rich terminal
ENV TERM=xterm-256color
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default Ollama host (points to docker service)
ENV OLLAMA_HOST=http://ollama:11434
ENV OLLAMA_MODEL=llama3.1

# Create directory for history persistence
RUN mkdir -p /root/.assistant_history

ENTRYPOINT ["python", "-m", "src.main"]
