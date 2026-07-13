#!/bin/bash
set -e
PY=/app/.venv/bin/python

if [ $# -gt 0 ]; then
    # CLI mode: arguments provided, wayfinder CLI
    exec "$PY" -m src "$@"
else
    # Web mode: no arguments, Streamlit UI
    exec /app/.venv/bin/streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
fi
