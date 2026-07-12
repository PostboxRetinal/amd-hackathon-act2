"""Entry point: python3 -m src "your prompt here" --json"""

import json
import os
import sys

# Ensure FIREWORKS_API_KEY is set
if not os.environ.get("FIREWORKS_API_KEY"):
    print("ERROR: FIREWORKS_API_KEY environment variable is required")
    sys.exit(1)

from src.router import Router


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
