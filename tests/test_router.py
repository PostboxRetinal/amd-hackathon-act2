"""Tests for the Router model selection and fallback logic."""

from unittest.mock import patch

from src.router import Router
from src.tasks import TaskCategory


class TestSelectModel:
    """Tests for Router.select_model task-to-model mapping."""

    def test_math_uses_gemma_9b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.MATH)
        assert model.name == "gemma-4-9b"

    def test_code_uses_deepseek(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.CODE)
        assert model.name == "deepseek-v4-pro"

    def test_reasoning_uses_glm5p2(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.REASONING)
        assert model.name == "glm-5p2"

    def test_factoid_uses_gemma_9b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.FACTOID)
        assert model.name == "gemma-4-9b"

    def test_summarization_uses_gemma_26b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.SUMMARIZATION)
        assert model.name == "gemma-4-26b"

    def test_creative_uses_gemma_26b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.CREATIVE)
        assert model.name == "gemma-4-26b"

    def test_extraction_uses_gemma_9b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.EXTRACTION)
        assert model.name == "gemma-4-9b"

    def test_classification_uses_gemma_9b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.CLASSIFICATION)
        assert model.name == "gemma-4-9b"

    def test_unknown_uses_gemma_9b(self):
        router = Router(api_key="test")
        model = router.select_model(TaskCategory.UNKNOWN)
        assert model.name == "gemma-4-9b"


class TestRouteWithMock:
    """Tests for Router.route() with mocked _call."""

    @patch.object(Router, "_call")
    def test_route_uses_correct_model_for_math(self, mock_call):
        mock_call.return_value = ("The answer is 42.", 10, 5)
        router = Router(api_key="test")
        result = router.route("Calculate 6 * 7")
        assert result["model"] == "gemma-4-9b"

    @patch.object(Router, "_call")
    def test_route_uses_deepseek_for_code(self, mock_call):
        mock_call.return_value = ("```python\ndef f(): pass\n```", 10, 20)
        router = Router(api_key="test")
        result = router.route("Write a Python function")
        assert result["model"] == "deepseek-v4-pro"

    @patch.object(Router, "_call")
    def test_route_uses_gemma_9b_for_factoid(self, mock_call):
        mock_call.return_value = ("Paris.", 5, 1)
        router = Router(api_key="test")
        result = router.route("What is the capital of France?")
        assert result["model"] == "gemma-4-9b"

    @patch.object(Router, "_call")
    def test_route_uses_glm_for_reasoning(self, mock_call):
        mock_call.return_value = (
            "Therefore, the conclusion follows from the premise.",
            10,
            20,
        )
        router = Router(api_key="test")
        result = router.route("Explain why the sky is blue")
        assert result["model"] == "glm-5p2"

    @patch.object(Router, "_call")
    def test_route_falls_back_when_score_low(self, mock_call):
        mock_call.side_effect = [
            ("huh?", 5, 2),
            ("The answer is 42 because 6 times 7 equals 42.", 10, 15),
        ]
        router = Router(api_key="test")
        result = router.route("Calculate 6 * 7")
        assert result["accuracy_score"] >= 0.7
        assert result["fallback_used"] is True


class TestFallbackChain:
    """Tests for Router._fallback_chain()."""

    def test_fallback_excludes_current_model(self):
        router = Router(api_key="test")
        current = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(current)
        assert all(m.name != current.name for m in chain)

    def test_fallback_includes_all_available_models(self):
        router = Router(api_key="test")
        current = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(current)
        all_models = router._all()
        expected = [m for m in all_models if m.name != current.name and m.provider != "vllm"]
        assert len(chain) == len(expected)

    def test_fallback_excludes_unavailable_local(self):
        router = Router(api_key="test")
        current = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(current)
        for m in chain:
            if m.provider == "vllm":
                assert router._is_local_available()

    def test_fallback_sorted_by_cost(self):
        router = Router(api_key="test")
        current = router.select_model(TaskCategory.MATH)
        chain = router._fallback_chain(current)
        costs = [m.cost_per_1k_tokens for m in chain]
        assert costs == sorted(costs)


class TestLocalModelFallback:
    """Tests for local model availability checks in select_model."""

    def test_does_not_return_local_model_when_unavailable(self):
        router = Router(api_key="test")
        assert not router._is_local_available()
        model = router.select_model(TaskCategory.MATH)
        assert model.provider != "vllm"

    def test_local_available_returns_local_for_cheap_tasks(self):
        router = Router(api_key="test")
        router._local_checked = True
        router._local_available = True
        model = router.select_model(TaskCategory.MATH)
        assert model.name == "gemma-4-9b"


class TestCallUsesApiKey:
    """Tests that the API key is properly used."""

    def test_api_key_from_parameter(self):
        router = Router(api_key="my-secret-key")
        assert router.api_key == "my-secret-key"

    def test_api_key_from_env(self):
        import os

        old_key = os.environ.get("FIREWORKS_API_KEY", "")
        os.environ["FIREWORKS_API_KEY"] = "env-key-123"
        try:
            router = Router()
            assert router.api_key == "env-key-123"
        finally:
            os.environ["FIREWORKS_API_KEY"] = old_key


def test_router_stats_tracking():
    """Router should track call statistics."""
    router = Router(api_key="test")
    assert router.stats["total_calls"] == 0
    assert router.stats["total_tokens"] == 0
    assert router.stats["falls_back"] == 0
    assert router.stats["cost"] == 0.0


def test_token_count_estimate():
    """_count_tokens should estimate ~4 chars per token."""
    assert Router._count_tokens("hello world!") == 3
    assert Router._count_tokens("") == 0
    assert Router._count_tokens("abcd") == 1


def test_router_cache():
    """Router should cache results for identical prompts."""
    with patch.object(Router, "_call") as mock_call:
        mock_call.return_value = ("The answer is 42.", 10, 5)
        router = Router(api_key="test")
        result1 = router.route("Calculate 6 * 7")
        result2 = router.route("Calculate 6 * 7")
        assert mock_call.call_count == 1
        assert result1 == result2


def test_router_selects_cheapest_for_factoid():
    """Factoid tasks should use the cheapest suitable model (gemma-4-9b)."""
    router = Router(api_key="test")
    model = router.select_model(TaskCategory.FACTOID)
    assert model.name == "gemma-4-9b"
    gemma26b = next(m for m in router._all() if m.name == "gemma-4-26b")
    assert model.cost_per_1k_tokens < gemma26b.cost_per_1k_tokens


def test_router_selects_fast_for_code():
    """Code tasks should use deepseek-v4-pro."""
    router = Router(api_key="test")
    model = router.select_model(TaskCategory.CODE)
    assert model.name == "deepseek-v4-pro"
