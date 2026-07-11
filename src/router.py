import json
import os
import subprocess
from typing import Optional

from src.models import Model, ModelTier
from src.tasks import TaskCategory, classify_task
from src.evaluator import evaluate_response


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

        # Cache hit on cheapest model?
        cache_key = f"{model.name}:{hash(prompt)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        chain = [model] + self._fallback_chain(model)
        best = None

        for attempt in chain:
            response = self._call(attempt, prompt)
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
        self.stats["total_tokens"] += best["tokens"]
        self.stats["cost"] += best["cost"]
        return best

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _call(self, model: Model, prompt: str) -> str:
        """Call the model via Fireworks API."""
        payload = {
            "model": model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
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
            return data["choices"][0]["message"]["content"]
        except (KeyError, json.JSONDecodeError):
            return "[ERROR]"

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
