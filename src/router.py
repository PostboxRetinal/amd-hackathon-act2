import hashlib
import json
import os
import socket
import subprocess

from src.evaluator import evaluate_response
from src.models import Model, ModelTier
from src.tasks import TaskCategory, classify_task

# Per-category max_tokens — smaller for concise tasks, larger for code/reasoning.
MAX_TOKENS_BY_CATEGORY: dict[TaskCategory, int] = {
    TaskCategory.FACTOID: 2048,
    TaskCategory.MATH: 2048,
    TaskCategory.CODE: 4096,
    TaskCategory.REASONING: 4096,
    TaskCategory.CLASSIFICATION: 2048,
    TaskCategory.EXTRACTION: 2048,
    TaskCategory.SUMMARIZATION: 2048,
    TaskCategory.CREATIVE: 4096,
    TaskCategory.UNKNOWN: 2048,
}

# Default vLLM endpoint for health-check probing.
_VLLM_HOST = os.environ.get("VLLM_HOST", "localhost")
_VLLM_PORT = int(os.environ.get("VLLM_PORT", "8000"))


class Router:
    """
    Token-efficient router that selects the cheapest model for each task,
    validates response quality, and escalates to larger models when needed.
    """

    def __init__(self, api_key: str | None = None):
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
    #  Task-aware model selection
    # ------------------------------------------------------------------

    # Maps each task category to the model name that is best suited for it,
    # balancing cost and capability.  The values must match the "name" field
    # in config/models.yaml.
    _TASK_MODEL_MAP: dict[TaskCategory, str] = {
        TaskCategory.MATH: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.FACTOID: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.CLASSIFICATION: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.EXTRACTION: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.SUMMARIZATION: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.UNKNOWN: "gemma-4-e4b-local",  # 0 FW tokens
        TaskCategory.CREATIVE: "gemma-4-26b",  # dedicated deploy
        TaskCategory.CODE: "deepseek-v4-pro",  # strong coder
        TaskCategory.REASONING: "glm-5p2",  # strongest reasoning
    }

    def select_model(self, task: TaskCategory) -> Model:
        """
        Pick the best model for the task category.

        Strategy:
          - Use a task-to-model strength map (cost-aware: cheapest suitable model first).
          - If the recommended model is a local vLLM model that is unavailable,
            fall back to the next suitable model by tier.
        """
        model_name = self._TASK_MODEL_MAP.get(task, "gemma-4-26b")
        model = self._get_model_by_name(model_name)

        # If the recommended model is a local vLLM instance that is not running,
        # fall back to the cheapest available Fireworks model.
        if self._is_local_model(model) and not self._is_local_available():
            model = self._cheapest_available_fireworks_model()

        return model

    def _fallback_chain(self, current: Model) -> list[Model]:
        """
        Models to try in order if the current one fails.

        Returns all *other* models sorted by cost (cheapest first), excluding
        local vLLM models that are not available so we don't waste time on
        dead endpoints.
        """
        all_models = self._all()
        candidates = [
            m
            for m in all_models
            if m.name != current.name
            and not (self._is_local_model(m) and not self._is_local_available())
        ]
        # Sort by cost_per_1k_tokens so we always try the cheapest viable model first.
        candidates.sort(key=lambda m: m.cost_per_1k_tokens)
        return candidates

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
            if response.startswith("[ERROR") and self._is_local_model(attempt):
                continue

            tokens = prompt_tok + completion_tok
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
                "model": "none",
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

    def _call(self, model: Model, prompt: str, max_tokens: int = 512) -> tuple[str, int, int]:
        """Call the model via Fireworks API or local server. Returns (response, prompt_tokens, completion_tokens)."""
        payload = {
            "model": model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        # Build curl command based on provider.
        if model.provider.lower() == "local":
            # Local model: model.model_id is the full URL; omit auth header.
            url = model.model_id
            headers = ["-H", "Content-Type: application/json"]
        else:
            # Fireworks model: use Fireworks endpoint with auth header.
            # Check for missing API key before attempting the call.
            if not self.api_key:
                return (
                    "[ERROR: FIREWORKS_API_KEY not set. Set the FIREWORKS_API_KEY environment variable.]",
                    0,
                    0,
                )
            url = "https://api.fireworks.ai/inference/v1/chat/completions"
            headers = [
                "-H",
                f"Authorization: Bearer {self.api_key}",
                "-H",
                "Content-Type: application/json",
            ]

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X",
                    "POST",
                    url,
                    *headers,
                    "-d",
                    json.dumps(payload),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            if model.provider.lower() == "local":
                return f"[ERROR: Local model at {url} timed out after 60 seconds]", 0, 0
            return "[ERROR: Fireworks API request timed out after 60 seconds]", 0, 0
        except OSError as e:
            if model.provider.lower() == "local":
                return f"[ERROR: Cannot connect to local model at {url} - {e.strerror}]", 0, 0
            return f"[ERROR: Connection error to Fireworks API - {e.strerror}]", 0, 0

        try:
            data = json.loads(result.stdout)
            content = data["choices"][0]["message"]["content"]
            if content is None:
                return "[ERROR: Fireworks API returned null content]", 0, 0
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            return content, prompt_tokens, completion_tokens
        except (KeyError, json.JSONDecodeError, TypeError, AttributeError):
            # Check if API returned an error message in its response body.
            try:
                err_data = json.loads(result.stdout)
                err_msg = err_data.get("error", {})
                if isinstance(err_msg, dict):
                    err_msg = err_msg.get("message", "Unknown API error")
                return f"[ERROR: Fireworks API - {err_msg}]", 0, 0
            except (json.JSONDecodeError, AttributeError, TypeError):
                if model.provider.lower() == "local":
                    return f"[ERROR: Failed to parse response from local model at {url}]", 0, 0
                return "[ERROR: Failed to parse Fireworks API response]", 0, 0

    # ------------------------------------------------------------------
    #  Local model helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_local_model(model: Model) -> bool:
        """Return True if the model is served by a local vLLM instance."""
        return model.provider.lower() in ("vllm", "local")

    def _is_local_available(self) -> bool:
        """
        Quick TCP probe to check whether the local vLLM server is running.
        Result is cached after the first check to avoid repeated probes.
        """
        if self._local_checked:
            return self._local_available

        self._local_checked = True
        try:
            with socket.create_connection((_VLLM_HOST, _VLLM_PORT), timeout=1.0):
                self._local_available = True
        except (TimeoutError, OSError):
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
    def _get_model_by_name(name: str) -> Model:
        """Return the model with the given name from the catalog."""
        from src.models import MODEL_CATALOG

        for m in MODEL_CATALOG:
            if m.name == name:
                return m
        # Fallback: return the first non-local model if name not found
        for m in MODEL_CATALOG:
            if m.provider != "vllm":
                return m
        raise ValueError(f"Model '{name}' not found and no fallback available")

    def _cheapest_available_fireworks_model(self) -> Model:
        """Return the cheapest available non-local model (Fireworks)."""
        candidates = [m for m in self._all() if not self._is_local_model(m)]
        if not candidates:
            # No non-local models — return the first model as last resort
            return self._all()[0]
        candidates.sort(key=lambda m: m.cost_per_1k_tokens)
        return candidates[0]

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
    print("---")
    print(result["response"])


if __name__ == "__main__":
    main()
