#!/bin/bash
set -e

# If arguments are provided, execute them instead of entering prompt mode
if [ $# -gt 0 ]; then
    exec "$@"
fi

echo "=== Wayfinder — Hybrid Token-Efficient Routing Agent ==="
echo ""

if [ -t 0 ]; then
    # Interactive mode
    echo "Enter a prompt (Ctrl+D to exit):"
    while read -r -p "> " prompt; do
        uv run python -m src "$prompt"
    done
else
    # Pipe/batch mode
    while read -r line; do
        uv run python -m src "$line"
    done
fi
