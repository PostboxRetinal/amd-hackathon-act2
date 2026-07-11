from dataclasses import dataclass
from enum import Enum


class ModelTier(Enum):
    CHEAP = "cheap"
    FAST = "fast"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class Model:
    name: str
    tier: ModelTier
    provider: str  # "fireworks" | "vllm"
    model_id: str  # fireworks model ID or vLLM served name
    cost_per_1k_tokens: float  # USD
    accuracy_score: float  # 0-1 estimated baseline
    context_limit: int


MODEL_CATALOG: list[Model] = [
    Model(
        name="gemma-4-9b",
        tier=ModelTier.FAST,
        provider="fireworks",
        model_id="accounts/fireworks/models/gemma-4-9b-it",
        cost_per_1k_tokens=0.0002,
        accuracy_score=0.82,
        context_limit=16000,
    ),
    Model(
        name="gemma-4-26b",
        tier=ModelTier.STANDARD,
        provider="fireworks",
        model_id="accounts/fireworks/models/gemma-4-26b-a4b-it",
        cost_per_1k_tokens=0.0005,
        accuracy_score=0.91,
        context_limit=32000,
    ),
    Model(
        name="gemma-4-31b",
        tier=ModelTier.PREMIUM,
        provider="fireworks",
        model_id="accounts/fireworks/models/gemma-4-31b-it",
        cost_per_1k_tokens=0.001,
        accuracy_score=0.95,
        context_limit=260000,
    ),
    Model(
        name="deepseek-v4-pro",
        tier=ModelTier.STANDARD,
        provider="fireworks",
        model_id="accounts/fireworks/models/deepseek-v4-pro",
        cost_per_1k_tokens=0.0015,
        accuracy_score=0.93,
        context_limit=1000000,
    ),
    Model(
        name="glm-5p2",
        tier=ModelTier.PREMIUM,
        provider="fireworks",
        model_id="accounts/fireworks/models/glm-5p2",
        cost_per_1k_tokens=0.0014,
        accuracy_score=0.94,
        context_limit=1000000,
    ),
    Model(
        name="gemma-4-26b-local",
        tier=ModelTier.CHEAP,
        provider="vllm",
        model_id="gemma-4-26b",
        cost_per_1k_tokens=0.0,
        accuracy_score=0.91,
        context_limit=32000,
    ),
    Model(
        name="gemma-4-9b-local",
        tier=ModelTier.CHEAP,
        provider="vllm",
        model_id="gemma-4-9b",
        cost_per_1k_tokens=0.0,
        accuracy_score=0.82,
        context_limit=16000,
    ),
]


def get_model(name: str) -> Model:
    for m in MODEL_CATALOG:
        if m.name == name:
            return m
    raise ValueError(f"Model '{name}' not found")


def get_models_by_tier(tier: ModelTier) -> list[Model]:
    return [m for m in MODEL_CATALOG if m.tier == tier]


def get_models_by_provider(provider: str) -> list[Model]:
    return [m for m in MODEL_CATALOG if m.provider == provider]
