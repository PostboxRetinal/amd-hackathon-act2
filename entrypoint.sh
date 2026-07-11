#!/bin/bash
# Entrypoint for the routing agent container.
# Reads prompts from stdin and routes through Fireworks.

set -e

echo "=== Hybrid Token-Efficient Routing Agent ==="
echo ""

if [ -t 0 ]; then
    # Interactive mode
    echo "Enter a prompt (Ctrl+D to exit):"
    while read -r -p "> " prompt; do
        uv run python -m src "$prompt"
    done
else
    # Pipe mode
    while read -r line; do
        uv run python -m src.router "$line"
    done
fi
