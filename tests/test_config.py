"""Basic test that config/models.yaml exists and has the right structure."""


def test_models_yaml_exists():
    """models.yaml exists."""
    import os

    assert os.path.isfile("config/models.yaml")


def test_models_yaml_has_required_fields():
    """Each model entry has required fields."""
    import yaml

    with open("config/models.yaml") as f:
        raw = yaml.safe_load(f)
    data = raw["models"] if isinstance(raw, dict) else raw
    assert isinstance(data, list)
    required = {"name", "display_name", "provider", "model_id"}
    for entry in data:
        assert required.issubset(set(entry.keys())), f"Missing in {entry['name']}"


def test_models_yaml_non_negative_cost():
    """All cost_per_1k_tokens are >= 0."""
    import yaml

    with open("config/models.yaml") as f:
        raw = yaml.safe_load(f)
    data = raw["models"] if isinstance(raw, dict) else raw
    for entry in data:
        cost = entry.get("cost_per_1k_tokens", 0)
        assert cost >= 0, f"{entry['name']} has negative cost: {cost}"
