# ---- Build stage ----
FROM python:3.13-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --extra web && rm -rf /root/.cache/uv

# ---- Runtime stage ----
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv .venv/

COPY src/ src/
COPY config/ config/
COPY app/ app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

# Auto-detect: args → CLI, no args → Web UI
ENTRYPOINT ["/entrypoint.sh"]
