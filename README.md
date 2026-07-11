# Hybrid Token-Efficient Routing Agent

> AMD Developer Hackathon: ACT II — Track 1

## Overview

An intelligent routing agent that selects the cheapest **Fireworks AI** model for every task, minimizing token usage without sacrificing accuracy. It uses **Gemma 4** (Google DeepMind) alongside other models to classify tasks, run inference, evaluate response quality, and escalate to larger models only when necessary.

Eligible for the **$1,000 Gemma Prize** (Google DeepMind).

## Architecture

```
Task → Classifier → Is it a simple task?
                     ├── Yes → CHEAP model (0 Fireworks tokens)
                     └── No → FAST model → Evaluator → Score ≥ 0.7?
                                                            ├── Yes → ✅ Return
                                                            └── No → Escalate: STANDARD → PREMIUM
```

## Model Catalog

| Model | Tier | Provider | Cost |
|---|---|---|---|
| Gemma 4 9B | FAST | Fireworks | $0.0002/K |
| Gemma 4 26B | STANDARD | Fireworks | $0.0005/K |
| Gemma 4 31B | PREMIUM | Fireworks | $0.001/K |
| GLM 5.2 | PREMIUM | Fireworks | $0.0014/K |
| DeepSeek V4 Pro | STANDARD | Fireworks | $0.0015/K |

## Quick Start

```bash
# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your API key
export FIREWORKS_API_KEY="fw_..."

# Run the router
python3 -m src.router "What is the capital of Japan?"

# Run tests
pytest tests/ -v

# Benchmark models
python3 scripts/benchmark.py
```

## Docker

```bash
docker build -t amd-router .
docker run -e FIREWORKS_API_KEY="fw_..." amd-router
```

## Scoring Strategy

The router uses a **fallback chain**: it starts with the cheapest model tier and escalates if the response quality score is below 0.7. This minimizes Fireworks token consumption while maintaining accuracy.

- Local models (vLLM-served on AMD GPUs) cost **0 Fireworks tokens**
- Each response is evaluated using heuristics for correctness, conciseness, and task fit
- Cache hit responses skip inference entirely

## Submission Requirements

- [x] Public GitHub repository
- [x] Containerized (Dockerfile)
- [x] README with setup/usage instructions
- [ ] Demo video
- [ ] Submission form on lablab.ai

## Tech Stack

- **Fireworks AI** — Serverless inference API
- **AMD GPU Cloud** — On-demand GPU deployment
- **Gemma 4** — Google DeepMind models
- **vLLM** — Local model serving (optional)
- **Python 3.10** — Core runtime
