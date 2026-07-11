import hashlib
import json
import os
import socket
import subprocess
from typing import Optional

from src.models import Model, ModelTier
from src.tasks import TaskCategory, classify_task
from src.evaluator import evaluate_response

# Per-category max_tokens — smaller for concise tasks, larger for code/reasoning.
MAX_TOKENS_BY_CATEGORY: dict[TaskCategory, int] = {
    TaskCategory.FACTOID: 100,
    TaskCategory.MATH: 150,
    TaskCategory.CODE: 1024,
    TaskCategory.REASONING: 1024,
    TaskCategory.CLASSIFICATION: 256,
    TaskCategory.EXTRACTION: 512,
    TaskCategory.SUMMARIZATION: 512,
    TaskCategory.CREATIVE: 512,
    TaskCategory.UNKNOWN: 512,
}

# Default vLLM endpoint for health-check probing.
_VLLM_HOST = os.environ.get("VLLM_HOST", "localhost")
_VLLM_PORT = int(os.environ.get("VLLM_PORT", "8000"))


class Router:
    """
    Token-efficient router that selects the cheapest model for each task,
    validates response quality, and escalates to larger models when needed.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY", "")
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "falls_back": 0,
            "cost": 0.0,
        }
        self.cache: dict[str, dict] = {}
        # Cache local-availability result so we only probe once per session.
        self._local_checked: bool = False
        self._local_available: bool = False

    # ------------------------------------------------------------------
    #  Public helpers (used by tests)
    # ------------------------------------------------------------------

    def _task_type(self, prompt: str) -> TaskCategory:
        """Classify a prompt. Public helper for testing."""
        return classify_task(prompt)

    def _cache_key(self, model_name: str, prompt: str) -> str:
        """Generate cache key. Public helper for testing."""
        return f"{model_name}:{hash(prompt)}"

    # ------------------------------------------------------------------
    #  Model selection
    # ------------------------------------------------------------------

    def select_model(self, task: TaskCategory) -> Model:
        """Pick the cheapest model tier suitable for this task category."""

        # Tasks that small models handle reliably
        if task in (
            TaskCategory.FACTOID,
            TaskCategory.CLASSIFICATION,
            TaskCategory.EXTRACTION,
            TaskCategory.MATH,
        ):
            return self._pick(ModelTier.CHEAP)

        return self._pick(ModelTier.FAST)

    def _fallback_chain(self, current: Model) -> list[Model]:
        """Models to try in order if the current one fails."""
        tiers = list(ModelTier)
        current_index = next(i for i, t in enumerate(tiers) if t == current.tier)
        return [
            m
            for t in tiers[current_index + 1:]
            for m in self._all()
            if m.tier == t
        ]

    # ------------------------------------------------------------------
    #  Routing
    # ------------------------------------------------------------------

    def route(self, prompt: str) -> dict:
        """
        Route a single prompt through the cheapest → best model chain.

        Returns a result dict with:
            response, model, tokens, cost, accuracy_score, fallback_used
        """
        self.stats["total_calls"] += 1

        task = classify_task(prompt)
        model = self.select_model(task)
        max_tokens = MAX_TOKENS_BY_CATEGORY.get(task, 512)

        # Cache hit on cheapest model?
        cache_key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if cache_key in self.cache:
            return self.cache[cache_key]

        chain = [model] + self._fallback_chain(model)
        best = None

        for attempt in chain:
            # Skip vLLM (local) models that are unavailable so we don't
            # waste time evaluating an [ERROR] placeholder.
            if self._is_local_model(attempt) and not self._is_local_available():
                continue

            response, prompt_tok, completion_tok = self._call(
                attempt, prompt, max_tokens=max_tokens
            )

            # If a local model returned an error, skip to next tier immediately.
            if response == "[ERROR]" and self._is_local_model(attempt):
                continue

            tokens = self._count_tokens(response)
            score = evaluate_response(prompt, response, task)

            if score >= 0.7:
                result = {
                    "response": response,
                    "model": attempt.name,
                    "tokens": tokens,
                    "cost": tokens * attempt.cost_per_1k_tokens / 1000,
                    "accuracy_score": score,
                    "fallback_used": attempt is not model,
                }
                if attempt is model:
                    self.cache[cache_key] = result
                self.stats["total_tokens"] += tokens
                self.stats["cost"] += result["cost"]
                if attempt is not model:
                    self.stats["falls_back"] += 1
                return result

            best = {
                "response": response,
                "model": attempt.name,
                "tokens": tokens,
                "cost": tokens * attempt.cost_per_1k_tokens / 1000,
                "accuracy_score": score,
                "fallback_used": True,
            }

        # All models failed — return the best of the worst
        if best is None:
            return {
                "response": "All models failed",
                "tokens": 0,
                "cost": 0.0,
                "accuracy_score": 0.0,
                "fallback_used": True,
            }
        self.stats["total_tokens"] += best["tokens"]
        self.stats["cost"] += best["cost"]
        return best

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _call(
        self, model: Model, prompt: str, max_tokens: int = 512
    ) -> tuple[str, int, int]:
        """Call the model via Fireworks API. Returns (response, prompt_tokens, completion_tokens)."""
        payload = {
            "model": model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "https://api.fireworks.ai/inference/v1/chat/completions",
                "-H", f"Authorization: Bearer {self.api_key}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        try:
            data = json.loads(result.stdout)
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            return content, prompt_tokens, completion_tokens
        except (KeyError, json.JSONDecodeError):
            return "[ERROR]", 0, 0

    # ------------------------------------------------------------------
    #  Local model helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_local_model(model: Model) -> bool:
        """Return True if the model is served by a local vLLM instance."""
        return model.provider.lower() == "vllm"

    def _is_local_available(self) -> bool:
        """
        Quick TCP probe to check whether the local vLLM server is running.
        Result is cached after the first check to avoid repeated probes.
        """
        if self._local_checked:
            return self._local_available

        self._local_checked = True
        try:
            with socket.create_connection(
                (_VLLM_HOST, _VLLM_PORT), timeout=1.0
            ):
                self._local_available = True
        except (OSError, socket.timeout):
            self._local_available = False
        return self._local_available

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Rough estimate: ~4 chars per token."""
        return len(text) // 4

    @staticmethod
    def _pick(tier: ModelTier) -> Model:
        from src.models import MODEL_CATALOG
        for m in MODEL_CATALOG:
            if m.tier == tier:
                return m
        raise ValueError(f"No model for tier {tier}")

    @staticmethod
    def _all() -> list[Model]:
        from src.models import MODEL_CATALOG
        return MODEL_CATALOG


def main() -> None:
    """CLI entry point for `python -m src.router`."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.router <prompt>", file=sys.stderr)
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])
    router = Router()
    result = router.route(prompt)
    print(f"Model:   {result['model']}")
    print(f"Tokens:  {result['tokens']}")
    print(f"Cost:    ${result['cost']:.6f}")
    print(f"Score:   {result['accuracy_score']:.2f}")
    print(f"---")
    print(result['response'])


if __name__ == "__main__":
    main()
