"""
Local evaluation harness for the routing agent.
Runs the router against a set of benchmark prompts and generates a report.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import MODEL_CATALOG
from src.router import Router

BENCHMARK_SUITE = [
    # Math
    ("math", "Calculate 1,234 + 5,678"),
    ("math", "What is 15% of 200?"),
    ("math", "If x = 5 and y = 3, what is 2x + 3y?"),
    # Code
    ("code", "Write a Python function to reverse a string"),
    ("code", "Create a function that checks if a number is prime"),
    ("code", "Write a bash one-liner to count lines in all .txt files"),
    # Factoid
    ("factoid", "What is the capital of Japan?"),
    ("factoid", "Who wrote Romeo and Juliet?"),
    ("factoid", "What is the chemical symbol for gold?"),
    # Reasoning
    ("reasoning", "If all humans are mortal and Socrates is human, is Socrates mortal?"),
    ("reasoning", "Explain why ice floats on water"),
    # Summarization
    (
        "summarization",
        "Summarize: Python is a high-level, interpreted programming language known for its readability and versatility. It supports multiple paradigms including object-oriented, functional, and procedural programming.",
    ),
    # Extraction
    (
        "extraction",
        "Extract all email addresses from: Contact john@example.com or support@test.org for help.",
    ),
    # Unknown / creative
    ("creative", "Tell me a short sci-fi story about a rogue AI"),
]


def run_benchmark(router: Router) -> dict:
    """Run the full benchmark suite and return results."""
    results = []
    total_tokens = 0
    total_cost = 0.0
    falls_back = 0
    gemma_prize_count = 0

    total = len(BENCHMARK_SUITE)
    for idx, (category, prompt) in enumerate(BENCHMARK_SUITE, 1):
        print(f'[{idx}/{total}] Testing: "{prompt}"...', file=sys.stderr, flush=True)
        start = time.time()
        result = router.route(prompt)
        elapsed = time.time() - start

        if "gemma" in result["model"]:
            gemma_prize_count += 1

        results.append(
            {
                "category": category,
                "prompt": prompt[:80],
                "model": result["model"],
                "tokens": result["tokens"],
                "cost": result["cost"],
                "accuracy": round(result["accuracy_score"], 2),
                "fallback": result["fallback_used"],
                "time_s": round(elapsed, 2),
            }
        )
        total_tokens += result["tokens"]
        total_cost += result["cost"]
        if result["fallback_used"]:
            falls_back += 1

    return {
        "summary": {
            "total_prompts": len(results),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "falls_back": falls_back,
            "models_used": len(set(r["model"] for r in results)),
            "gemma_prize_count": gemma_prize_count,
        },
        "results": results,
    }


def print_report(report: dict):
    """Pretty-print the benchmark report."""
    s = report["summary"]
    print("=" * 72)
    print(f"  EVALUATION REPORT -- {s['total_prompts']} prompts")
    print("=" * 72)
    print(f"  Total tokens:  {s['total_tokens']}")
    print(f"  Total cost:    ${s['total_cost']:.6f}")
    print(f"  Fallbacks:     {s['falls_back']}/{s['total_prompts']}")
    print(f"  Models used:   {s['models_used']}")
    print("-" * 72)
    print(
        f"  {'#':>3} {'Category':<14} {'Model':<20} {'Tok':>5} {'Cost':>8} {'Acc':>4} {'Time':>5}  {'Status':<10}"
    )
    print("-" * 72)
    for i, r in enumerate(report["results"], 1):
        status = "FALLBACK" if r["fallback"] else "PASS"
        print(
            f"  {i:>3} {r['category']:<14} {r['model']:<20} {r['tokens']:>5d} ${r['cost']:<6.4f} {r['accuracy']:.2f} {r['time_s']:>4.1f}s  {status:<10}"
        )
    print("=" * 72)
    gemma_count = s.get("gemma_prize_count", 0)
    if gemma_count > 0:
        print(
            f"  Gemma Prize: YES (gemma model used in {gemma_count}/{s['total_prompts']} prompts)"
        )
    else:
        print("  Gemma Prize: NO (no gemma model used)")


def main():
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        print("ERROR: FIREWORKS_API_KEY not set")
        print("Usage: FIREWORKS_API_KEY=fw_... uv run python scripts/evaluate.py")
        sys.exit(1)

    print(f"Loaded {len(MODEL_CATALOG)} models from config/models.yaml")
    print()

    router = Router(api_key=api_key)
    report = run_benchmark(router)
    print_report(report)

    # Save to JSON
    out_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "evaluation-report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
