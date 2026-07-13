"""Tests for model catalog loading (src/models.py)."""

from src.models import get_model, load_models


def test_loads_all_models():
    """load_models returns all 6 model entries."""
    models = load_models()
    assert len(models) == 6


def test_model_fields_populated():
    """Each model has name, display_name, provider."""
    for m in load_models():
        assert m.name
        assert m.display_name
        assert m.provider


def test_get_model_found():
    """get_model returns a matching model by name."""
    m = get_model("deepseek-v4-pro")
    assert m is not None
    assert m.name == "deepseek-v4-pro"


def test_get_model_not_found_raises():
    """get_model raises ValueError for unknown names."""
    import pytest

    with pytest.raises(ValueError, match="not found"):
        get_model("nonexistent-model")
