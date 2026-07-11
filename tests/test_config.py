"""Test model catalog YAML loading."""
import os
import yaml


def test_models_yaml_exists():
    path = os.path.join(os.path.dirname(__file__), "..", "config", "models.yaml")
    assert os.path.exists(path), f"File not found: {path}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


def test_models_yaml_has_required_fields():
    path = os.path.join(os.path.dirname(__file__), "..", "config", "models.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    required = {"name", "tier", "provider", "model_id", "cost_per_1k_tokens"}
    for i, model in enumerate(data["models"]):
        missing = required - set(model.keys())
        assert not missing, f"Model #{i} missing: {missing}"


def test_models_yaml_valid_tiers():
    valid = {"cheap", "fast", "standard", "premium"}
    path = os.path.join(os.path.dirname(__file__), "..", "config", "models.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    for model in data["models"]:
        assert model["tier"] in valid, f"Invalid tier: {model['tier']}"
