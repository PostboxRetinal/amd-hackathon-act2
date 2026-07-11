# Configurable Fallback Threshold

## Goal
Allow the user to configure the accuracy threshold that triggers model fallback, instead of the hardcoded 0.7.

## What Changes
- Add `threshold` parameter to `Router.__init__()`
- Update evaluator to use configurable threshold
- Load default from `config/models.yaml` or env var
- Add CLI flag in `__main__.py`

## Capabilities
- **New:** `configurable-threshold` — user can set accuracy threshold per session
- **Modified:** router routing logic uses dynamic threshold instead of constant

## Impact
- `src/router.py` — `select_model()` and `route()` need threshold param
- `src/evaluator.py` — no changes needed (returns score, doesn't decide)
- `config/models.yaml` — add `default_threshold: 0.7`
- `src/__main__.py` — add `--threshold` flag
