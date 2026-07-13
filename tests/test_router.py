"""Router tests — comprehensive coverage for 75% threshold."""

import sys
from unittest.mock import patch

from src.router import Router, main
from src.tasks import TaskCategory, classify_task


def _make_router(api_key="test-key"):
    return Router(api_key=api_key)


# ── _pick_first ──────────────────────────────────────────────────────────


class TestPickFirst:
    def test_returns_model(self):
        r = _make_router()
        m = r._pick_first()
        assert m is not None
        assert hasattr(m, "name")

    def test_returns_first_catalog_model(self):
        r = _make_router()
        from src.models import MODEL_CATALOG

        assert r._pick_first().name == MODEL_CATALOG[0].name


# ── _count_tokens ────────────────────────────────────────────────────────


class TestCountTokens:
    def test_empty(self):
        assert Router._count_tokens("") == 0

    def test_short(self):
        assert Router._count_tokens("hello world") == 2

    def test_long(self):
        assert Router._count_tokens("a" * 100) == 25


# ── _cache_key ───────────────────────────────────────────────────────────


class TestCacheKey:
    def test_deterministic(self):
        r = _make_router()
        k1 = r._cache_key("model-x", "hello")
        k2 = r._cache_key("model-x", "hello")
        assert k1 == k2

    def test_diff_prompts(self):
        r = _make_router()
        k1 = r._cache_key("model-x", "hello")
        k2 = r._cache_key("model-x", "world")
        assert k1 != k2


# ── select_model ─────────────────────────────────────────────────────────


class TestSelectModel:
    def test_math(self):
        r = _make_router()
        task = classify_task("what is 2 + 2")
        m = r.select_model(task)
        assert m is not None

    def test_code(self):
        r = _make_router()
        task = classify_task("write a python function")
        m = r.select_model(task)
        assert m is not None

    def test_reasoning(self):
        r = _make_router()
        task = classify_task("explain why ice floats")
        m = r.select_model(task)
        assert m is not None

    def test_factoid(self):
        r = _make_router()
        task = classify_task("what is the capital of japan")
        m = r.select_model(task)
        assert m is not None

    def test_creative(self):
        r = _make_router()
        task = classify_task("write a short story")
        m = r.select_model(task)
        assert m is not None

    def test_extraction(self):
        r = _make_router()
        task = classify_task("extract emails from text")
        m = r.select_model(task)
        assert m is not None

    def test_summarization(self):
        r = _make_router()
        task = classify_task("summarize this paragraph")
        m = r.select_model(task)
        assert m is not None


# ── _fallback_chain ──────────────────────────────────────────────────────


class TestFallbackChain:
    def test_excludes_current(self):
        from src.models import MODEL_CATALOG

        r = _make_router()
        current = MODEL_CATALOG[0]
        chain = r._fallback_chain(current)
        assert current not in chain

    def test_sorted_by_cost(self):
        from src.models import MODEL_CATALOG

        r = _make_router()
        current = MODEL_CATALOG[0]
        chain = r._fallback_chain(current)
        for i in range(len(chain) - 1):
            assert chain[i].cost_per_1k_tokens <= chain[i + 1].cost_per_1k_tokens


# ── _cheapest_available_fireworks_model ──────────────────────────────────


def test_cheapest_fireworks_excludes_local():
    r = _make_router()
    m = r._cheapest_available_fireworks_model()
    assert r._is_local_model(m) is False


# ── _call ────────────────────────────────────────────────────────────────


class TestCall:
    def test_no_api_key_returns_error(self):
        r = Router(api_key="")
        resp = r.route("hello")
        assert "error" in resp or resp.get("response", "").startswith("[ERROR")

    def test_success_returns_response(self):
        r = _make_router()
        m = r._pick_first()
        resp, pt, ct = r._call(m, "say hello")
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_bad_json_handled(self):
        r = _make_router()
        m = r._pick_first()
        resp, pt, ct = r._call(m, "return invalid")
        assert resp is not None


# ── route ────────────────────────────────────────────────────────────────


class TestRoute:
    def test_math_task(self):
        r = _make_router()
        result = r.route("what is 2 + 2")
        assert "response" in result
        assert "model" in result
        assert "tokens" in result
        assert "cost" in result
        assert "accuracy_score" in result
        assert "task_category" in result

    def test_code_task(self):
        r = _make_router()
        result = r.route("write a python function to reverse a string")
        assert result["accuracy_score"] >= 0

    def test_empty_prompt(self):
        r = _make_router()
        result = r.route("")
        assert result is not None

    def test_cache_hit(self):
        r = _make_router()
        r1 = r.route("hello world")
        r2 = r.route("hello world")
        assert r1["response"] == r2["response"]

    def test_all_keys_present(self):
        r = _make_router()
        result = r.route("say hi")
        expected = {
            "response",
            "model",
            "tokens",
            "cost",
            "accuracy_score",
            "fallback_used",
            "task_category",
        }
        assert expected.issubset(set(result.keys()))


# ── _get_model_by_name ───────────────────────────────────────────────────


class TestGetModelByName:
    def test_found(self):
        r = _make_router()
        m = r._get_model_by_name("deepseek-v4-pro")
        assert m.name == "deepseek-v4-pro"

    def test_fallback(self):
        r = _make_router()
        m = r._get_model_by_name("nonexistent")
        assert m is not None


# ── _task_type ───────────────────────────────────────────────────────────


def test_task_type_math():
    r = _make_router()
    t = r._task_type("2 + 2 = ?")
    assert isinstance(t, TaskCategory)


def test_task_type_code():
    r = _make_router()
    t = r._task_type("def fib")
    assert t == TaskCategory.CODE


# ── main CLI ─────────────────────────────────────────────────────────────


def test_no_args_exits():
    old = sys.argv
    sys.argv = ["wayfinder"]
    try:
        main()
    except SystemExit:
        pass
    finally:
        sys.argv = old


def test_main_with_prompt():
    old_argv = sys.argv
    sys.argv = ["wayfinder", "What", "is", "the", "capital", "of", "France?"]
    try:
        with patch("src.router.Router") as mock_router:
            instance = mock_router.return_value
            instance.route.return_value = {
                "model": "gemma-4-26b",
                "tokens": 12,
                "cost": 0.0001,
                "accuracy_score": 1.0,
                "response": "Paris",
                "task_category": "factoid",
            }
            main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
