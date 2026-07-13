#!/bin/bash
set -e

# venv is baked into the runtime image; call python directly (uv is build-only).
PY=/app/.venv/bin/python

# If arguments are provided, pass them to the Python CLI
if [ $# -gt 0 ]; then
    exec "$PY" -m src "$@"
fi

# No arguments: read from stdin (batch mode)
if [ -t 0 ]; then
    # Interactive mode
    echo "=== Wayfinder — Hybrid Token-Efficient Routing Agent ==="
    echo "Enter a prompt (Ctrl+D to exit):"
    while read -r -p "> " prompt; do
        "$PY" -m src "$prompt"
    done
else
    # Pipe/batch mode — read each line as a separate prompt
    while read -r line; do
        "$PY" -m src "$line"
    done
fi
