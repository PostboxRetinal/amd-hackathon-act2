# Configurable Fallback Threshold — Tasks

### T-001: Add threshold param to Router
**Status:** ⏳ Pending
**Files:** `src/router.py`
**Verification:** `Router(threshold=0.9).threshold == 0.9`

### T-002: Update route() to use dynamic threshold
**Status:** ⏳ Pending
**Files:** `src/router.py`
**Verification:** `route()` compares evaluator score against `self.threshold`

### T-003: Add default_threshold to YAML config
**Status:** ⏳ Pending
**Files:** `config/models.yaml`
**Verification:** `models.py` loads `default_threshold` field

### T-004: Add CLI --threshold flag
**Status:** ⏳ Pending
**Files:** `src/__main__.py`
**Verification:** `--threshold 0.5` overrides default

### T-005: Write tests
**Status:** ⏳ Pending
**Files:** `tests/test_router.py`
**Verification:** `pytest tests/test_router.py -v` passes

### T-006: Update README
**Status:** ⏳ Pending
**Files:** `README.md`
**Verification:** README documents `--threshold` flag
