# Configurable Fallback Threshold — Specs

## Requirement: Configurable threshold

### Description
The router SHALL accept a configurable accuracy threshold that determines when model fallback is triggered.

### Scenarios

#### Scenario: Default threshold used when none specified
WHEN Router is created without a threshold argument
THEN threshold SHALL default to 0.7
AND fallback SHALL trigger when evaluator score < 0.7

#### Scenario: Custom threshold via constructor
WHEN Router is created with threshold=0.9
THEN fallback SHALL trigger when evaluator score < 0.9

#### Scenario: CLI flag overrides default
WHEN `--threshold 0.5` is passed to `__main__.py`
THEN Router SHALL use 0.5 as the threshold

#### Scenario: Threshold from YAML config
WHEN `config/models.yaml` contains `default_threshold: 0.8`
AND no CLI flag or env var is set
THEN Router SHALL use 0.8 as the threshold
