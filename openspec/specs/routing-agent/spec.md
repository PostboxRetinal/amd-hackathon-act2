# Routing Agent — Specifications

## Purpose
Wayfinder is a hybrid token-efficient routing agent that distributes inference across multiple models (Gemma 4, DeepSeek V4 Pro, GLM 5.2) based on task category. It achieves 100% accuracy at $0.002/14 prompts with 51 tests and 87% coverage.

## Requirements

### Requirement: Task Classification
The system SHALL classify incoming prompts into predefined task categories.
- **Categories:** MATH, CODE, REASONING, FACTOID, CLASSIFICATION, SUMMARIZATION, EXTRACTION, CREATIVE, UNKNOWN
- **Accuracy threshold:** >= 80% on benchmark suite

#### Scenario: Math prompt classified as MATH
- **WHEN** the user submits "Calculate 1,234 + 5,678"
- **THEN** the system classifies it as MATH
- **AND** selects gemma-4-e4b-local as the primary model

#### Scenario: Code prompt classified as CODE
- **WHEN** the user submits "Write a Python function to reverse a string"
- **THEN** the system classifies it as CODE
- **AND** selects deepseek-v4-pro as the primary model

#### Scenario: Reasoning prompt classified as REASONING
- **WHEN** the user submits a multi-step logic puzzle
- **THEN** the system classifies it as REASONING
- **AND** selects glm-5p2 as the primary model

### Requirement: Model Selection
The router SHALL select the most cost-effective model suitable for the task category.
- **Model map:** math/factoid/classification/extraction/summarization/unknown -> gemma-4-e4b-local, code -> deepseek-v4-pro, reasoning -> glm-5p2, creative -> gemma-4-26b
- **Fallback:** If primary model fails, fall through to next cheapest tier

#### Scenario: Math prompt routes to gemma-4-e4b-local
- **WHEN** the task is MATH
- **THEN** the router selects gemma-4-e4b-local (cost: $0.00/1K tokens)
- **AND** if gemma-4-e4b-local is unavailable, falls back through the chain

#### Scenario: Code prompt routes to deepseek-v4-pro
- **WHEN** the task is CODE
- **THEN** the router selects deepseek-v4-pro
- **AND** if deepseek-v4-pro is unavailable, falls back through the chain

### Requirement: Response Evaluation
The system SHALL evaluate response quality and escalate to a higher-tier model if insufficient.
- **Acceptance threshold:** score >= 0.7
- **Escalation:** Try next model in fallback chain, repeat evaluation

#### Scenario: Low quality response triggers fallback
- **WHEN** the primary model returns a response with score < 0.7
- **THEN** the router tries the next model in the fallback chain

#### Scenario: High quality response accepted
- **WHEN** the primary model returns a response with score >= 0.7
- **THEN** the router accepts the response and returns it to the user

### Requirement: Token Tracking
The system SHALL track tokens consumed and cost per request.
- **Metrics:** tokens, cost ($), accuracy, model used, fallback indicator
- **Output:** Per-request result dict + cumulative stats

#### Scenario: Single request tracking
- **WHEN** the router processes a prompt
- **THEN** the result dict includes tokens, cost, accuracy_score, model, and fallback_used

### Requirement: Error Handling
The system SHALL return descriptive error messages instead of generic [ERROR] codes.

#### Scenario: Missing API key
- **WHEN** FIREWORKS_API_KEY is not set
- **THEN** the system returns "[ERROR: FIREWORKS_API_KEY not set...]"

#### Scenario: Local model unreachable
- **WHEN** a vLLM local model server is not running
- **THEN** the system returns a descriptive error with model URL context
- **AND** falls back to the next model in the chain

### Requirement: Configurability
The model catalog SHALL be editable without code changes.
- **Implementation:** `config/models.yaml`

#### Scenario: Add a new model without code changes
- **WHEN** the operator adds a model entry to config/models.yaml
- **THEN** the router picks it up on next load without any source code modification

### Requirement: Web Interface
The system SHALL provide a Streamlit web interface for interactive routing.

#### Scenario: User routes a prompt via web UI
- **WHEN** the user enters a prompt and clicks Route
- **THEN** the system displays the model, accuracy, tokens, cost, and response

#### Scenario: Cache hit returns same result
- **WHEN** the user submits the same prompt twice
- **THEN** the second request returns the cached result without calling the API again
