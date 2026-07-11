# Hybrid Token-Efficient Routing Agent

> AMD Developer Hackathon: ACT II — Track 1

## Overview

An intelligent routing agent that selects the cheapest available model for every task, minimizing token usage without sacrificing accuracy. It classifies tasks by type, runs inference on the cheapest suitable model, evaluates response quality, and falls back to larger models only when necessary.

The router supports both **Fireworks AI** (serverless cloud inference) and **vLLM** (local AMD GPU serving). Local models cost **0 Fireworks tokens** and are preferred when available; the router gracefully skips them when they're down.

Eligible for the **$1,000 Gemma Prize** with **9/14 prompts** routed through Gemma 4 26B (dedicated H200 GPU, autoscaling 0-1).

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
  │  Per-category max_tokens (factoid=2048, math=2048, code=4096, reasoning=4096)
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
| DeepSeek V4 Pro | STANDARD | Fireworks | $0.0015 |
| GLM 5.2 | PREMIUM | Fireworks | $0.0014 |
| Gemma 4 26B (dedicated H200) | CHEAP | Fireworks Deploy | $28/h (GPU) |

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

37 tests covering task classification, model catalog, evaluator, and router logic with 84% code coverage.

### Benchmark Results

| Metric | Value |
|---|---|
| Total prompts | 14 |
| Models used | 3 (gemma-4-26b, deepseek-v4-pro, glm-5p2) |
| Gemma 4 26B coverage | **9/14 prompts** (eligible for Gemma Prize) |
| Total tokens | 3,224 |
| Total cost | **$0.002111** |
| Accuracy | **100%** |
| Fallback rate | 2/14 |
| Evaluator threshold | 0.7 |
| GPU hours consumed | 2.54 (NVIDIA H200 141GB x4) |
| Total GPU cost | $71.12 @ $28/h |
| P50 latency | 1,000 ms |
| P99 latency | 11,800 ms |
| P50 TTFT | 15.5 ms |
| Output throughput | 13.9 tokens/s |
| Prompt cache hit rate | 58.5% |

## Scoring Strategy

The router uses a **fallback chain**: it starts with the cheapest model tier and escalates if the response quality score is below 0.7. This minimizes token consumption while maintaining accuracy.

- **Local models** (vLLM on AMD GPUs) cost **0 Fireworks tokens** — preferred when available
- **Per-category max_tokens** — factoid=2048, math=2048, code=4096, reasoning=4096 (Gemma 4 needs room for chain-of-thought)
- **Evaluator** penalizes `[ERROR]` responses and applies stronger penalties for code/math tasks; refusal keywords avoid false positives ("cannot" in code context)
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
3. `pytest --cov=src` — 37 tests, 85% coverage (threshold: 80%)

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
