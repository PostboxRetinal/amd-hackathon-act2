"""Tests for config/models.yaml structure and validity."""

import os

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "models.yaml")


def test_models_yaml_exists():
    """The models config file should exist."""
    assert os.path.isfile(CONFIG_PATH), f"models.yaml not found at {CONFIG_PATH}"


def test_models_yaml_has_required_fields():
    """Each model entry must have all required fields."""
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    required = {"name", "tier", "provider", "model_id", "cost_per_1k_tokens", "accuracy_score"}
    for model in data["models"]:
        for field in required:
            assert field in model, f"Model {model.get('name', '?')} missing field '{field}'"


def test_models_yaml_non_negative_cost():
    """All cost_per_1k_tokens values must be non-negative."""
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    for model in data["models"]:
        assert model["cost_per_1k_tokens"] >= 0, f"Model {model['name']} has negative cost"


def test_models_yaml_valid_tiers():
    """All tier values must be one of the valid ModelTier values."""
    valid_tiers = {"cheap", "fast", "standard", "premium"}
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    for model in data["models"]:
        assert model["tier"] in valid_tiers, (
            f"Model {model['name']} has invalid tier '{model['tier']}'"
        )
