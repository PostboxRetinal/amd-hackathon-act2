import json
import os
import sys
from importlib.metadata import version as _pkg_version

from src.router import Router

# Check --version before API key check
if "--version" in sys.argv:
    try:
        ver = _pkg_version("wayfinder")
    except Exception:
        ver = "0.5.0"
    print(f"wayfinder {ver}")
    sys.exit(0)

HELP_TEXT = """Wayfinder -- Hybrid Token-Efficient Routing Agent

Usage:
  wayfinder <prompt>              Route a prompt through the optimal model
  wayfinder <prompt> --json       Structured JSON output (for judging)
  wayfinder --version             Show version
  wayfinder --help                Show this help message

Requires FIREWORKS_API_KEY environment variable.

Examples:
  wayfinder "What is 2+2?"
  wayfinder "def fib(n): ..." --json
"""

if "--help" in sys.argv or "-h" in sys.argv:
    print(HELP_TEXT)
    sys.exit(0)

# No args: show help
if len(sys.argv) == 1:
    print(HELP_TEXT)
    sys.exit(0)

# Ensure FIREWORKS_API_KEY is set
if not os.environ.get("FIREWORKS_API_KEY"):
    print("ERROR: FIREWORKS_API_KEY environment variable is required")
    sys.exit(1)


def main():
    args = sys.argv[1:]

    # Check for --json flag
    json_mode = "--json" in args
    if json_mode:
        args = [a for a in args if a != "--json"]

    prompt = " ".join(args) if args else sys.stdin.read().strip()
    if not prompt:
        print("Usage: python3 -m src <prompt> [--json]")
        sys.exit(1)

    router = Router()
    result = router.route(prompt)

    if json_mode:
        # Structured JSON output for judging
        output = {
            "task_id": prompt[:64],
            "response": result["response"],
            "model": result["model"],
            "tokens": result["tokens"],
            "cost": round(result["cost"], 6),
            "accuracy": round(result["accuracy_score"], 2),
        }
        print(json.dumps(output))
        return

    # Human-readable output
    print(f"Model:         {result['model']}")
    print(f"Accuracy:      {result['accuracy_score']:.2f}")
    print(f"Tokens:        {result['tokens']}")
    print(f"Cost:          ${result['cost']:.6f}")
    print(f"Fallback used: {result['fallback_used']}")
    print("---")
    print(result["response"])


if __name__ == "__main__":
    main()
