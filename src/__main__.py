"""Entry point: python3 -m src.router "your prompt here" """

import os
import sys

# Ensure FIREWORKS_API_KEY is set
if not os.environ.get("FIREWORKS_API_KEY"):
    print("ERROR: FIREWORKS_API_KEY environment variable is required")
    sys.exit(1)

from src.router import Router


def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not prompt:
        print("Usage: python3 -m src.router <prompt>")
        sys.exit(1)

    router = Router()
    result = router.route(prompt)

    print(f"Model:         {result['model']}")
    print(f"Accuracy:      {result['accuracy_score']:.2f}")
    print(f"Tokens:        {result['tokens']}")
    print(f"Cost:          ${result['cost']:.6f}")
    print(f"Fallback used: {result['fallback_used']}")
    print(f"Response:      {result['response'][:200]}...")


if __name__ == "__main__":
    main()
