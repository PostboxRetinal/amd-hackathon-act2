"""Tests for Router class — model selection, fallback chain, caching, stats, and CLI."""

import sys
from unittest.mock import MagicMock

import pytest

from src.models import ModelTier
from src.router import Router


@pytest.fixture
def router():
    return Router(api_key="test-key")


class TestCountTokens:
    def test_empty(self, router):
        assert router._count_tokens("") == 0

    def test_short(self, router):
        assert router._count_tokens("hello") == 1

    def test_long(self, router):
        assert router._count_tokens("a" * 100) == 25


class TestCacheKey:
    def test_deterministic(self, router):
        assert router._cache_key("m", "p") == router._cache_key("m", "p")

    def test_diff_prompts(self, router):
        assert router._cache_key("m", "a") != router._cache_key("m", "b")


class TestTaskType:
    def test_math(self, router):
        assert router._task_type("Calculate 2+2").value == "math"


class TestPick:
    def test_cheap(self, router):
        assert router._pick(ModelTier.CHEAP).tier == ModelTier.CHEAP

    def test_fast(self, router):
        assert router._pick(ModelTier.FAST).tier == ModelTier.FAST


class TestSelectModel:
    def test_math(self, router):
        from src.tasks import TaskCategory

        assert router.select_model(TaskCategory.MATH).name == "gemma-4-26b"

    def test_code(self, router):
        from src.tasks import TaskCategory

        assert router.select_model(TaskCategory.CODE).name == "deepseek-v4-pro"

    def test_reasoning(self, router):
        from src.tasks import TaskCategory

        assert router.select_model(TaskCategory.REASONING).name == "glm-5p2"


class TestFallbackChain:
    def test_excludes_current(self, router):
        m = router._pick(ModelTier.CHEAP)
        assert m not in router._fallback_chain(m)

    def test_sorted_by_cost(self, router):
        m = router._pick(ModelTier.CHEAP)
        costs = [x.cost_per_1k_tokens for x in router._fallback_chain(m)]
        assert costs == sorted(costs)


class TestCall:
    def test_success(self, router, monkeypatch):
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(
                stdout='{"choices":[{"message":{"content":"ok"}}],'
                '"usage":{"prompt_tokens":1,"completion_tokens":1}}',
                returncode=0,
            ),
        )
        m = router._pick(ModelTier.FAST)
        r, pt, ct = router._call(m, "hi")
        assert r == "ok"

    def test_bad_json(self, router, monkeypatch):
        monkeypatch.setattr(
            "subprocess.run", lambda *a, **kw: MagicMock(stdout="bad", returncode=0)
        )
        m = router._pick(ModelTier.FAST)
        r, pt, ct = router._call(m, "hi")
        assert r == "[ERROR]"


class TestRouteEdgeCases:
    def test_stats(self, router, monkeypatch):
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(
                stdout='{"choices":[{"message":{"content":"ok"}}],'
                '"usage":{"prompt_tokens":1,"completion_tokens":1}}',
                returncode=0,
            ),
        )
        router.route("Say ok")
        assert router.stats["total_calls"] == 1

    def test_required_keys(self, router, monkeypatch):
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(
                stdout='{"choices":[{"message":{"content":"ok"}}],'
                '"usage":{"prompt_tokens":1,"completion_tokens":1}}',
                returncode=0,
            ),
        )
        r = router.route("Say ok")
        for k in ("response", "model", "tokens", "cost", "accuracy_score", "fallback_used"):
            assert k in r


class TestMain:
    def test_no_args_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["src.router"])
        with pytest.raises(SystemExit):
            from src.router import main

            main()

    def test_with_prompt(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["src.router", "hi"])
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(
                stdout='{"choices":[{"message":{"content":"ok"}}],'
                '"usage":{"prompt_tokens":1,"completion_tokens":1}}',
                returncode=0,
            ),
        )
        from src.router import main

        main()
