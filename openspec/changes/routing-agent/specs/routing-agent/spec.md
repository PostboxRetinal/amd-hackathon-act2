# Routing Agent — Specifications

## Functional Requirements

### FR-1: Task Classification
- **ID:** FR-001
- **Description:** System shall classify incoming prompts into predefined categories
- **Categories:** MATH, CODE, REASONING, FACTOID, CLASSIFICATION, SUMMARIZATION, EXTRACTION, CREATIVE, UNKNOWN
- **Accuracy:** ≥ 80% on benchmark suite
- **Verification:** `tests/test_tasks.py`

### FR-2: Model Selection
- **ID:** FR-002  
- **Description:** Router shall select cheapest model tier suitable for task
- **Logic:** CHEAP (local/vLLM) → FAST (Gemma 4 9B) → STANDARD (Gemma 4 26B) → PREMIUM (Gemma 4 31B, GLM 5.2)
- **Source:** `config/models.yaml`
- **Verification:** `tests/test_router.py`

### FR-3: Response Evaluation
- **ID:** FR-003
- **Description:** System shall evaluate response quality and escalate if insufficient
- **Threshold:** Accept if score ≥ 0.7
- **Escalation:** Try next tier model, repeat evaluation
- **Verification:** `tests/test_evaluator.py`

### FR-4: Token Tracking
- **ID:** FR-004
- **Description:** System shall track tokens consumed and cost per request
- **Metrics:** tokens, cost ($), accuracy, model used, fallback indicator
- **Output:** Per-request result dict + cumulative stats

### FR-5: Containerization
- **ID:** FR-005
- **Description:** Project must run in Docker container for standardized scoring
- **Base:** `python:3.10-slim`
- **Deps:** uv, PyYAML, requests, pytest

## Non-Functional Requirements

### NFR-1: Performance
- **ID:** NFR-001
- **Description:** Single inference should complete within 30s
- **Platform:** Fireworks API (latency may vary)

### NFR-2: Configurability
- **ID:** NFR-002
- **Description:** Model catalog must be editable without code changes
- **Implementation:** `config/models.yaml`

## API Contract

### `Router.route(prompt: str) -> dict`
- **Input:** `prompt` — task description string
- **Output:** `{response, model, tokens, cost, accuracy_score, fallback_used}`
- **Error:** Falls back through model chain; returns best-effort result
