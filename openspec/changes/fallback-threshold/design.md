# Configurable Fallback Threshold — Design

## Architecture

```
┌──────────────────┐      ┌──────────────────┐
│  __main__.py     │─────▶│  Router           │
│  --threshold 0.7 │      │  threshold=0.7    │
└──────────────────┘      └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Evaluator        │
                          │  returns score    │
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  score ≥ threshold│
                          │  ✅ accept / ❌ fallback│
                          └──────────────────┘
```

## Components

### Router
- New param: `threshold: float = 0.7`
- `route()` compares evaluator score against `self.threshold`
- Accessible via `__main__.py` CLI flag

### Config
- `config/models.yaml`: optional `default_threshold` field
- Env var: `ROUTER_THRESHOLD` override
- Priority: CLI flag > env var > YAML default > 0.7 hardcoded

## Data Flow
1. `Router(threshold=0.8)` created with threshold
2. `route(prompt)` runs classifier → model → evaluator
3. Evaluator returns score (unchanged)
4. Router compares `score >= self.threshold`
5. If false → escalate to next tier
6. If all tiers fail → return best effort
