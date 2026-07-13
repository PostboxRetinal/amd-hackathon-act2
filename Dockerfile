# ---- Build stage ----
FROM python:3.10-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev && rm -rf /root/.cache/uv

# ---- Runtime stage ----
FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /app/.venv .venv/

COPY src/ src/
COPY config/ config/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/entrypoint.sh"]
