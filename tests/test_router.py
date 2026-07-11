"""
Tests for the Router's task-aware model selection and fallback logic.
These tests run without any API calls — they verify the routing strategy
independently of Fireworks / vLLM availability.
"""

import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.router import Router
from src.models import Model, ModelTier, MODEL_CATALOG
from src.tasks import TaskCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router():
    """Router with a dummy API key and vLLM marked unavailable."""
    r = Router(api_key="test-key")
    r._local_checked = True
    r._local_available = False
    return r


# ---------------------------------------------------------------------------
# select_model: task-to-model mapping
# ---------------------------------------------------------------------------

class TestSelectModel:
    """Verify that select_model() maps each task to the correct model."""

    def test_math_uses_gemma_9b(self, router):
        """MATH should route to gemma-4-9b (cheap, fast, good at arithmetic)."""
        model = router.select_model(TaskCategory.MATH)
        assert model.name == "gemma-4-9b"

    def test_factoid_uses_gemma_9b(self, router):
        """FACTOID should route to gemma-4-9b."""
        model = router.select_model(TaskCategory.FACTOID)
        assert model.name == "gemma-4-9b"

    def test_classification_uses_gemma_9b(self, router):
        """CLASSIFICATION should route to gemma-4-9b."""
        model = router.select_model(TaskCategory.CLASSIFICATION)
        assert model.name == "gemma-4-9b"

    def test_extraction_uses_gemma_9b(self, router):
        """EXTRACTION should route to gemma-4-9b."""
        model = router.select_model(TaskCategory.EXTRACTION)
        assert model.name == "gemma-4-9b"

    def test_code_uses_deepseek(self, router):
        """CODE should route to deepseek-v4-pro (strong coder)."""
        model = router.select_model(TaskCategory.CODE)
        assert model.name == "deepseek-v4-pro"

    def test_reasoning_uses_glm5p2(self, router):
        """REASONING should route to glm-5p2 (strongest reasoning)."""
        model = router.select_model(TaskCategory.REASONING)
        assert model.name == "glm-5p2"

    def test_creative_uses_gemma_26b(self, router):
        """CREATIVE should route to gemma-4-26b (good balance)."""
        model = router.select_model(TaskCategory.CREATIVE)
        assert model.name == "gemma-4-26b"

    def test_summarization_uses_gemma_26b(self, router):
        """SUMMARIZATION should route to gemma-4-26b."""
        model = router.select_model(TaskCategory.SUMMARIZATION)
        assert model.name == "gemma-4-26b"

    def test_unknown_uses_gemma_9b(self, router):
        """UNKNOWN should default to gemma-4-9b (cheap default)."""
        model = router.select_model(TaskCategory.UNKNOWN)
        assert model.name == "gemma-4-9b"


# ---------------------------------------------------------------------------
# select_model: local vLLM fallback
# ---------------------------------------------------------------------------

class TestLocalModelFallback:
    """When vLLM is unavailable, select_model should not return a local model."""

    def test_does_not_return_local_model_when_unavailable(self, router):
        """No task should return a vLLM model when vLLM is not running."""
        for task in TaskCategory:
            model = router.select_model(task)
            assert model.provider != "vllm", (
                f"Task {task.name} returned local vLLM model {model.name} "
                f"when vLLM is unavailable"
            )

    def test_local_available_returns_local_for_cheap_tasks(self):
        """When vLLM IS available, cheap tasks should use the local model."""
        r = Router(api_key="test-key")
        r._local_checked = True
        r._local_available = True

        # Override the task map to use the local model for MATH
        original_map = Router._TASK_MODEL_MAP.copy()
        try:
            Router._TASK_MODEL_MAP[TaskCategory.MATH] = "gemma-4-9b-local"
            model = r.select_model(TaskCategory.MATH)
            assert model.provider == "vllm"
            assert model.name == "gemma-4-9b-local"
        finally:
            Router._TASK_MODEL_MAP = original_map


# ---------------------------------------------------------------------------
# _fallback_chain: cost-ordered, excludes unavailable local models
# ---------------------------------------------------------------------------

class TestFallbackChain:
    """Verify the fallback chain is cost-ordered and skips dead endpoints."""

    def test_fallback_excludes_current_model(self, router):
        """The fallback chain should not include the current model."""
        model = router.select_model(TaskCategory.CODE)
        chain = router._fallback_chain(model)
        assert model.name not in [m.name for m in chain]

    def test_fallback_excludes_unavailable_local(self, router):
        """Fallback chain should skip local vLLM models when vLLM is down."""
        model = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(model)
        for m in chain:
            assert m.provider != "vllm"

    def test_fallback_sorted_by_cost(self, router):
        """Fallback chain should be sorted cheapest-first."""
        model = router.select_model(TaskCategory.CODE)
        chain = router._fallback_chain(model)
        costs = [m.cost_per_1k_tokens for m in chain]
        assert costs == sorted(costs), f"Costs not sorted: {costs}"

    def test_fallback_includes_all_available_models(self, router):
        """Fallback chain should include all available models except current."""
        model = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(model)
        available = [
            m for m in MODEL_CATALOG
            if m.name != model.name and m.provider != "vllm"
        ]
        assert len(chain) == len(available), (
            f"Expected {len(available)} fallback models, got {len(chain)}"
        )


# ---------------------------------------------------------------------------
# Integration: full route() with mocked API calls
# ---------------------------------------------------------------------------

class TestRouteWithMock:
    """Test route() with _call() mocked to avoid real API calls."""

    def test_route_uses_correct_model_for_math(self, router, monkeypatch):
        """route() should use gemma-4-9b for math and not fall back."""
        def mock_call(self, model, prompt, max_tokens=512):
            return "6912", 10, 5  # Correct answer for "Calculate 1,234 + 5,678"
        monkeypatch.setattr(Router, "_call", mock_call)

        result = router.route("Calculate 1,234 + 5,678")
        assert result["model"] == "gemma-4-9b"
        assert result["fallback_used"] is False
        assert result["accuracy_score"] >= 0.7

    def test_route_falls_back_when_score_low(self, router, monkeypatch):
        """route() should fall back when the first model produces a low score."""
        call_count = {"n": 0}

        def mock_call(self, model, prompt, max_tokens=512):
            call_count["n"] += 1
            # All models return a bad response until glm-5p2 (last resort)
            if model.name == "glm-5p2":
                return "def reverse(s): return s[::-1]", 10, 5
            return "I cannot help with that.", 10, 8
        monkeypatch.setattr(Router, "_call", mock_call)

        result = router.route("Write a Python function to reverse a string")
        # Should fall through all models to glm-5p2 (last successful)
        assert result["model"] == "glm-5p2"
        assert result["fallback_used"] is True

    def test_route_uses_gemma_9b_for_factoid(self, router, monkeypatch):
        """route() should use gemma-4-9b for factoid questions."""
        def mock_call(self, model, prompt, max_tokens=512):
            return "Tokyo", 10, 3
        monkeypatch.setattr(Router, "_call", mock_call)

        result = router.route("What is the capital of Japan?")
        assert result["model"] == "gemma-4-9b"
        assert result["fallback_used"] is False

    def test_route_uses_deepseek_for_code(self, router, monkeypatch):
        """route() should use deepseek-v4-pro for code generation."""
        def mock_call(self, model, prompt, max_tokens=512):
            return "```python\ndef reverse(s):\n    return s[::-1]\n```", 10, 20
        monkeypatch.setattr(Router, "_call", mock_call)

        result = router.route("Write a Python function to reverse a string")
        assert result["model"] == "deepseek-v4-pro"
        assert result["fallback_used"] is False

    def test_route_uses_glm_for_reasoning(self, router, monkeypatch):
        """route() should use glm-5p2 for reasoning tasks."""
        def mock_call(self, model, prompt, max_tokens=512):
            return "Yes, Socrates is mortal. Since all humans are mortal and Socrates is human, therefore Socrates is mortal.", 10, 30
        monkeypatch.setattr(Router, "_call", mock_call)

        result = router.route("Explain why Socrates is mortal given that all humans are mortal and Socrates is human")
        assert result["model"] == "glm-5p2"


# ---------------------------------------------------------------------------
# _call() uses the real API key (not hardcoded "***")
# ---------------------------------------------------------------------------

class TestCallUsesApiKey:
    """Verify _call() passes the actual API key, not a placeholder."""

    def test_call_uses_self_api_key(self, monkeypatch):
        """_call() should pass self.api_key in the Authorization header."""
        captured_args = []

        def mock_run(*args, **kwargs):
            captured_args.extend(args[0])  # args[0] is the command list
            class MockResult:
                stdout = '{"choices":[{"message":{"content":"test"}}],"usage":{"prompt_tokens":5,"completion_tokens":5}}'
            return MockResult()

        monkeypatch.setattr("subprocess.run", mock_run)

        router = Router(api_key="fw_my_secret_key")
        router._local_checked = True
        router._local_available = False

        model = MODEL_CATALOG[1]  # gemma-4-9b (Fireworks)
        router._call(model, "test prompt")

        # Find the Authorization header in the captured args
        auth_header = None
        for i, arg in enumerate(captured_args):
            if arg == "-H" and i + 1 < len(captured_args):
                if "Authorization" in captured_args[i + 1]:
                    auth_header = captured_args[i + 1]
                    break

        assert auth_header is not None, "No Authorization header found"
        assert "fw_my_secret_key" in auth_header
        assert "***" not in auth_header
