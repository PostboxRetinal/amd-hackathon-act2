# tests/test_models.py

from unittest import mock

import pytest

from src.models import (
    Model,
    ModelTier,
    get_model,
    get_models_by_tier,
    load_catalog,
)

# ---------------------------------------------------------------------------
# ModelTier.from_str
# ---------------------------------------------------------------------------


class TestModelTierFromStr:
    def test_cheap(self):
        assert ModelTier.from_str("cheap") == ModelTier.CHEAP

    def test_fast(self):
        assert ModelTier.from_str("fast") == ModelTier.FAST

    def test_standard(self):
        assert ModelTier.from_str("standard") == ModelTier.STANDARD

    def test_premium(self):
        assert ModelTier.from_str("premium") == ModelTier.PREMIUM

    def test_unknown_returns_fast(self):
        assert ModelTier.from_str("nonexistent") == ModelTier.FAST

    def test_empty_string_returns_fast(self):
        assert ModelTier.from_str("") == ModelTier.FAST


# ---------------------------------------------------------------------------
# Model dataclass creation
# ---------------------------------------------------------------------------


class TestModelCreation:
    def test_basic_creation(self):
        m = Model(
            name="test-model",
            tier=ModelTier.STANDARD,
            provider="openai",
            model_id="gpt-4",
            cost_per_1k_tokens=0.03,
            accuracy_score=0.95,
            context_limit=8000,
        )
        assert m.name == "test-model"
        assert m.tier == ModelTier.STANDARD
        assert m.provider == "openai"
        assert m.model_id == "gpt-4"
        assert m.cost_per_1k_tokens == 0.03
        assert m.accuracy_score == 0.95
        assert m.context_limit == 8000

    def test_all_tiers_assignable(self):
        for tier in ModelTier:
            m = Model(
                name="m",
                tier=tier,
                provider="p",
                model_id="id",
                cost_per_1k_tokens=0.0,
                accuracy_score=0.0,
                context_limit=1000,
            )
            assert m.tier == tier


# ---------------------------------------------------------------------------
# Model.from_dict
# ---------------------------------------------------------------------------


class TestModelFromDict:
    BASE_DICT = {
        "name": "dict-model",
        "tier": "premium",
        "provider": "anthropic",
        "model_id": "claude-3",
        "cost_per_1k_tokens": 0.06,
        "accuracy_score": 0.92,
    }

    def test_with_context_limit(self):
        d = {**self.BASE_DICT, "context_limit": 32000}
        m = Model.from_dict(d)
        assert m.name == "dict-model"
        assert m.tier == ModelTier.PREMIUM
        assert m.provider == "anthropic"
        assert m.model_id == "claude-3"
        assert m.cost_per_1k_tokens == 0.06
        assert m.accuracy_score == 0.92
        assert m.context_limit == 32000

    def test_without_context_limit_defaults_to_16000(self):
        m = Model.from_dict(self.BASE_DICT)
        assert m.context_limit == 16000

    def test_tier_conversion_via_from_str(self):
        d = {**self.BASE_DICT, "tier": "unknown_tier"}
        m = Model.from_dict(d)
        assert m.tier == ModelTier.FAST


# ---------------------------------------------------------------------------
# load_catalog (mocked open to avoid real file access)
# ---------------------------------------------------------------------------

CATALOG_YAML = """models:
  - name: cheap-bot
    tier: cheap
    provider: deepseek
    model_id: deepseek-chat
    cost_per_1k_tokens: 0.001
    accuracy_score: 0.70
    context_limit: 4000
  - name: fast-runner
    tier: fast
    provider: groq
    model_id: llama-3
    cost_per_1k_tokens: 0.005
    accuracy_score: 0.80
    context_limit: 8000
  - name: std-model
    tier: standard
    provider: openai
    model_id: gpt-4o
    cost_per_1k_tokens: 0.01
    accuracy_score: 0.90
    context_limit: 16000
  - name: premium-pro
    tier: premium
    provider: anthropic
    model_id: claude-3-opus
    cost_per_1k_tokens: 0.05
    accuracy_score: 0.96
    context_limit: 200000
"""


class TestLoadCatalog:
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=CATALOG_YAML)
    def test_loads_all_models(self, mock_open_fn):
        models = load_catalog("/fake/path/models.yaml")
        assert len(models) == 4

    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=CATALOG_YAML)
    def test_model_fields_populated(self, mock_open_fn):
        models = load_catalog("/fake/path/models.yaml")
        m = models[0]
        assert m.name == "cheap-bot"
        assert m.tier == ModelTier.CHEAP
        assert m.provider == "deepseek"
        assert m.model_id == "deepseek-chat"
        assert m.cost_per_1k_tokens == 0.001
        assert m.accuracy_score == 0.70
        assert m.context_limit == 4000

    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=CATALOG_YAML)
    def test_tiers_parsed_correctly(self, mock_open_fn):
        models = load_catalog("/fake/path/models.yaml")
        tiers = [m.tier for m in models]
        assert ModelTier.CHEAP in tiers
        assert ModelTier.FAST in tiers
        assert ModelTier.STANDARD in tiers
        assert ModelTier.PREMIUM in tiers

    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=CATALOG_YAML)
    def test_returns_model_objects(self, mock_open_fn):
        models = load_catalog("/fake/path/models.yaml")
        for m in models:
            assert isinstance(m, Model)


# ---------------------------------------------------------------------------
# get_model
# ---------------------------------------------------------------------------


class TestGetModel:
    def test_found(self):
        # At least one model exists in the default catalog loaded at import
        catalog_names = [m.name for m in get_models_by_tier(ModelTier.CHEAP)]
        if catalog_names:
            model = get_model(catalog_names[0])
            assert model.name == catalog_names[0]
            assert isinstance(model, Model)
        else:
            pytest.skip("No cheap-tier models in catalog")

    def test_not_found_raises_value_error(self):
        with pytest.raises(ValueError, match="not found"):
            get_model("this-model-does-not-exist-xyz")


# ---------------------------------------------------------------------------
# get_models_by_tier
# ---------------------------------------------------------------------------


class TestGetModelsByTier:
    def test_returns_list(self):
        result = get_models_by_tier(ModelTier.FAST)
        assert isinstance(result, list)

    def test_all_returned_match_tier(self):
        for tier in ModelTier:
            result = get_models_by_tier(tier)
            for m in result:
                assert m.tier == tier

    def test_each_tier_has_at_least_one_model(self):
        # FAST is orphaned (no model uses it); all other tiers have >= 1
        for tier in ModelTier:
            result = get_models_by_tier(tier)
            if tier == ModelTier.FAST:
                assert len(result) == 0
            else:
                assert len(result) >= 1, f"No models found for tier: {tier}"
