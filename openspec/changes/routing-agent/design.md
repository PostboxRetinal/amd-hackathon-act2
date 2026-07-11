# Routing Agent — Design

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Prompt    │────▶│  Classifier   │────▶│    Router    │
└─────────────┘     └──────────────┘     └──────────────┘
                             │                    │
                             ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐
                    │ TaskCategory  │     │  ModelTier   │
                    │ MATH, CODE,  │     │ CHEAP, FAST, │
                    │ FACTOID...   │     │ STANDARD,... │
                    └──────────────┘     └──────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────┐
                                        │   Fallback Chain     │
                                        │ CHEAP → FAST → PREM  │
                                        └──────────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────┐
                                        │    Evaluator         │
                                        │  Score ≥ 0.7?       │
                                        └──────────────────────┘
```

## Components

### 1. Task Classifier (`src/tasks.py`)
- Heuristic-based classification
- Categories: MATH, CODE, REASONING, FACTOID, CLASSIFICATION, SUMMARIZATION, EXTRACTION, CREATIVE, UNKNOWN
- Threshold-based keyword matching

### 2. Model Router (`src/router.py`)
- Loads model catalog from `config/models.yaml`
- Selects cheapest model per task category
- Fallback chain: CHEAP → FAST → STANDARD → PREMIUM
- Response caching per model+prompt

### 3. Evaluator (`src/evaluator.py`)
- Heuristic response quality scorer
- Checks: refusal phrases, code content, numeric output, conciseness
- Returns score 0.0–1.0
- Threshold: ≥ 0.7 = accept

### 4. Model Catalog (`config/models.yaml`)
- External YAML config — no code changes to add models
- Fields: name, tier, provider, model_id, cost, accuracy, context

## Data Flow
1. Receive task prompt
2. Classify task type
3. Select cheapest model for that type
4. Execute inference (Fireworks API or local vLLM)
5. Evaluate response quality
6. If score < 0.7, escalate to next tier
7. Cache successful responses
8. Return response + metrics

## Scoring Strategy
- Local inference (vLLM on AMD GPUs) → 0 Fireworks tokens
- Fireworks API → measured token cost
- Router optimizes for min(tokens) subject to accuracy ≥ 0.7
- Benchmark against standardized eval suite
