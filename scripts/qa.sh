#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== ruff check ==="
uv tool run ruff check src/ tests/ scripts/
echo "PASS"
echo

echo "=== ruff format ==="
uv tool run ruff format --check src/ tests/ scripts/
echo "PASS"
echo

echo "=== pytest + coverage ==="
uv run python3 -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=75
echo "PASS"
echo

echo "=== All checks passed ==="
