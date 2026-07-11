# Routing Agent — Implementation

## Goal
Build an intelligent router that minimizes Fireworks AI tokens by selecting the cheapest model that maintains accuracy ≥ 0.7.

## Architecture
```
Prompt → Task Classifier → Select Model → Execute Inference → Evaluate Response
                                                                    ↓
                                                              Score ≥ 0.7?
                                                              ├── Yes → ✅ Return
                                                              └── No → Escalate to next tier
```

## Model Catalog

| Model | Provider | Cost | Context |
|---|---|---|---|
| Gemma 4 9B (local) | vLLM | $0 | 16K |
| Gemma 4 9B | Fireworks | $0.0002/K | 16K |
| Gemma 4 26B | Fireworks | $0.0005/K | 32K |
| DeepSeek V4 Pro | Fireworks | $0.0015/K | 1M |
| GLM 5.2 | Fireworks | $0.0014/K | 1M |

## Routing Strategy
1. **Classify** task (math, code, factoid, reasoning, etc.)
2. **Select** cheapest model suitable for that category
3. **Execute** inference
4. **Evaluate** quality (heuristic scorer 0-1)
5. If score < 0.7 → escalate to next tier
6. Cache responses from cheapest tier

## Success Criteria
- [ ] Router classifies correctly ≥ 8/10 categories
- [ ] Fallback chain escalates correctly
- [ ] All unit tests pass (current: 9/9)
- [ ] Benchmark produces token and cost report
- [ ] Docker container functional

## Files
- `src/router.py` — Core routing logic
- `src/models.py` — Model catalog (loads from YAML)
- `src/tasks.py` — Task classifier
- `src/evaluator.py` — Heuristic scorer
- `config/models.yaml` — Configurable model catalog
- `tests/` — Unit tests
- `scripts/evaluate.py` — Benchmark harness
- `scripts/benchmark.py` — Fireworks model benchmark
