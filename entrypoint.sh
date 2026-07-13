#!/bin/bash
set -e
PY=/app/.venv/bin/python

if [ $# -gt 0 ]; then
    # CLI mode: arguments provided → run wayfinder
    exec "$PY" -m src "$@"
else
    # Web mode: no arguments → run Streamlit UI
    cd /app
    PYTHONPATH=/app exec /app/.venv/bin/streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
fi
