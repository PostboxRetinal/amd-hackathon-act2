FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set link mode to avoid cross-filesystem warning
ENV UV_LINK_MODE=copy

# Copy project config
COPY pyproject.toml .
COPY uv.lock .

# Install all deps including dev (pytest, pytest-cov)
RUN uv sync --dev --frozen

# Copy source code
COPY src/ src/
COPY scripts/ scripts/
COPY config/ config/
COPY tests/ tests/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
