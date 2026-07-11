"""
Benchmark models on Fireworks API.
Measures tokens per response + accuracy per task category.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import MODEL_CATALOG, Model
from src.tasks import TaskCategory
from src.evaluator import evaluate_response

# Test prompts — one per category
TEST_PROMPTS: dict[TaskCategory, list[str]] = {
    TaskCategory.MATH: [
        "Calculate 1,234 + 5,678",
        "What is 15% of 200?",
    ],
    TaskCategory.CODE: [
        "Write a Python function to reverse a string",
        "Create a function that checks if a number is prime",
    ],
    TaskCategory.FACTOID: [
        "What is the capital of Japan?",
        "Who wrote Romeo and Juliet?",
    ],
    TaskCategory.REASONING: [
        "If all humans are mortal and Socrates is human, is Socrates mortal?",
    ],
    TaskCategory.SUMMARIZATION: [
        "Summarize: Python is a high-level programming language known for readability.",
    ],
}


def call_fireworks(model: Model, prompt: str, api_key: str) -> tuple[str, int, float]:
    """Call model via Fireworks API. Returns (response, tokens, elapsed_seconds)."""
    payload = {
        "model": model.model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.1,
    }
    start = time.time()
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://api.fireworks.ai/inference/v1/chat/completions",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    elapsed = time.time() - start

    try:
        data = json.loads(result.stdout)
        content = data["choices"][0]["message"]["content"]
        tokens = (data["usage"]["completion_tokens"]
                  if "usage" in data else len(content) // 4)
    except (KeyError, json.JSONDecodeError):
        content = "[ERROR]"
        tokens = 0
        elapsed = 0

    return content, tokens, elapsed


def main():
    api_key = os.environ.get("FIREWORKS_API_KEY", "")
    if not api_key:
        print("ERROR: FIREWORKS_API_KEY not set")
        sys.exit(1)

    # Only test Fireworks models (skip local/vllm entries)
    models = [m for m in MODEL_CATALOG if m.provider == "fireworks"]

    print(f"{'Model':30s} {'Category':15s} {'Score':>6s} {'Tokens':>8s} {'Time':>6s}")
    print("-" * 70)

    for model in models:
        for category, prompts in TEST_PROMPTS.items():
            for prompt in prompts:
                response, tokens, elapsed = call_fireworks(model, prompt, api_key)
                score = evaluate_response(prompt, response, category)
                print(f"{model.name:30s} {category.value:15s} {score:6.2f} {tokens:8d} {elapsed:5.1f}s")
            time.sleep(0.5)  # Rate-limit politeness


if __name__ == "__main__":
    main()
