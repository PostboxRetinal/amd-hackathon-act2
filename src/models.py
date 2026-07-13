from __future__ import annotations

import os
from dataclasses import dataclass

import yaml


@dataclass
class Model:
    name: str
    provider: str
    model_id: str
    cost_per_1k_tokens: float
    accuracy_score: float = 0.0
    context_limit: int = 0
    display_name: str = ""
    local_model_name: str = ""
    category: str = ""
    model_url: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> Model:
        return cls(
            name=d["name"],
            provider=d["provider"],
            model_id=d["model_id"],
            cost_per_1k_tokens=d["cost_per_1k_tokens"],
            accuracy_score=d.get("accuracy_score", 0.0),
            context_limit=d.get("context_limit", 16000),
            display_name=d.get("display_name", d.get("name", "")),
            local_model_name=d.get("local_model_name", ""),
            category=d.get("category", ""),
            model_url=d.get("model_url", ""),
        )


def load_catalog(path: str | None = None) -> list[Model]:
    """Load model catalog from YAML config file."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "config", "models.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    return [Model.from_dict(m) for m in data["models"]]


# Default catalog — loaded from YAML once on import
MODEL_CATALOG: list[Model] = load_catalog()


def load_models() -> list[Model]:
    """Return the full model catalog loaded from YAML config."""
    return MODEL_CATALOG


def get_model(name: str) -> Model:
    for m in MODEL_CATALOG:
        if m.name == name:
            return m
    raise ValueError(f"Model '{name}' not found in catalog")
