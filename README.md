# Hybrid Token-Efficient Routing Agent

> AMD Developer Hackathon: ACT II — Track 1

## Overview

An intelligent routing agent that selects the cheapest available model for every task, minimizing token usage without sacrificing accuracy. It classifies tasks by type, runs inference on the cheapest suitable model, evaluates response quality, and falls back to larger models only when necessary.

The router supports both **Fireworks AI** (serverless cloud inference) and **vLLM** (local AMD GPU serving). Local models cost **0 Fireworks tokens** and are preferred when available; the router gracefully skips them when they're down.

Eligible for the **$1,000 Gemma Prize** (Google DeepMind).

## Architecture

```
Prompt
  │
  ▼
Task Classifier (src/tasks.py)
  │  → factoid | math | code | reasoning
  ▼
Router (src/router.py)
  │  Selects cheapest model for category
  │  Per-category max_tokens (factoid=100, math=150, code=1024, reasoning=1024)
  ▼
┌─────────────────────────────────┐
│  Local model available (vLLM)?  │
│  YES → Try local first (0 cost) │
│  NO  → Skip gracefully          │
└─────────────────────────────────┘
  │
  ▼
Fireworks Inference (cheapest tier)
  │
  ▼
Evaluator (src/evaluator.py)
  │  Scores response 0.0–1.0
  │  Penalizes [ERROR] responses
  │  Stronger penalties for code/math
  ▼
Score ≥ 0.7?
  ├── YES → [OK] Return response
  └── NO  → Escalate to next tier
            FAST → STANDARD → PREMIUM
            (best=None guard prevents crashes)
```

## Tech Stack

- **Language:** Python 3.10
- **Package Manager:** uv
- **Cloud Inference:** Fireworks AI
- **Local Inference:** vLLM (AMD ROCm 7.2)
- **Testing:** pytest

## Model Catalog

| Model | Tier | Provider | Cost ($/K tokens) |
|---|---|---|---|
| Gemma 4 9B (local) | FAST | vLLM / AMD GPU | $0.00 |
| Gemma 4 9B | FAST | Fireworks | $0.0002 |
| Gemma 4 26B | STANDARD | Fireworks | $0.0005 |
| Gemma 4 31B | PREMIUM | Fireworks | $0.0010 |
| DeepSeek V4 Pro | STANDARD | Fireworks | $0.0015 |
| GLM 5.2 | PREMIUM | Fireworks | $0.0014 |

## Quick Start

### Prerequisites

- Python 3.10
- [uv](https://docs.astral.sh/uv/) package manager
- Fireworks AI API key
- (Optional) AMD GPU with ROCm 7.2 + vLLM for local inference

### Setup

```bash
# Clone the repo
git clone <repo-url> && cd amd-hackathon-act2

# Create virtual environment with Python 3.10
uv venv -p 3.10
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Set your API key
export FIREWORKS_API_KEY="fw_..."
```

### Usage

```bash
# Run the router with a prompt
uv run python -m src "<prompt>"

# Example
uv run python -m src "What is the capital of Japan?"
uv run python -m src "Write a Python function to reverse a list"
uv run python -m src "Solve: 3x + 7 = 22"
```

### Evaluation

```bash
uv run python scripts/evaluate.py
```

Runs the full evaluation suite across all categories and models, producing a JSON report with scores and token counts.

### Tests

```bash
uv run python3 -m pytest tests/ -v
```

17 tests covering task classification, model catalog, evaluator, and router logic.

## Scoring Strategy

The router uses a **fallback chain**: it starts with the cheapest model tier and escalates if the response quality score is below 0.7. This minimizes token consumption while maintaining accuracy.

- **Local models** (vLLM on AMD GPUs) cost **0 Fireworks tokens** — preferred when available
- **Per-category max_tokens** — factoid=100, math=150, code=1024, reasoning=1024 (prevents over-generation)
- **Evaluator** penalizes `[ERROR]` responses and applies stronger penalties for code/math tasks
- **Graceful degradation** — local models are skipped automatically when unavailable
- **best=None guard** — prevents crashes when no model produces an acceptable response

## Tech Stack

- **Python 3.10** — Core runtime
- **uv** — Dependency management
- **Fireworks AI** — Serverless cloud inference (5 models)
- **vLLM** — Local model serving on AMD GPUs
- **ROCm 7.2** — AMD GPU compute platform
- **Gemma 4** — Google DeepMind models (9B/26B/31B)
- **Pytest** — Testing framework
- **Ruff** — Python linter and formatter

## Quality Assurance

This project includes automated QA via a **pre-commit hook** that runs on every commit:

```bash
# Run QA manually (same checks as the hook):
uv run qa

# Or directly:
bash scripts/qa.sh
```

The QA pipeline checks:
1. `ruff check` — Lint errors, unused imports, naming conventions
2. `ruff format --check` — Code formatting consistency
3. `pytest` — All 45+ tests pass

If any check fails, the commit is blocked. To bypass (not recommended):
```bash
git commit --no-verify -m "message"
```

To set up the hook in a fresh clone:
```bash
cp scripts/qa.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Project Structure

```
amd-hackathon-act2/
├── src/
│   ├── __init__.py
│   ├── tasks.py       # Task classifier (factoid/math/code/reasoning)
│   ├── models.py      # Model catalog loader
│   ├── evaluator.py   # Response quality evaluator
│   └── router.py      # Core routing logic with fallback chain
├── config/
│   └── models.yaml    # Model definitions (tier, cost, provider)
├── scripts/
│   ├── benchmark.py   # Model benchmarking
│   └── evaluate.py    # Full evaluation suite
├── tests/
│   ├── test_tasks.py
│   ├── test_config.py
│   ├── test_evaluator.py
│   └── test_router.py
├── openspec/
│   └── changes/routing-agent/tasks.md
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── README.md
```

## Submission

- **Deadline:** Sunday, July 12, 2026 — 3:00 PM PT
- **Track:** Track 1 — Token-Efficient Routing
