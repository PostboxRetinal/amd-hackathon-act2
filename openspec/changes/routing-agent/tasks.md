# Routing Agent — Tasks

## Task List

### T-001: Setup project structure
**Status:** Complete
**Files:** `.gitignore`, `Dockerfile`, `entrypoint.sh`, `requirements.txt`, `config/models.yaml`
**Verification:** `git status` shows tracked files

### T-002: Write task classifier (`src/tasks.py`)
**Status:** Complete
**Files:** `src/tasks.py`, `tests/test_tasks.py`
**Verification:** `pytest tests/test_tasks.py -v` — 6/6 pass

### T-003: Write model catalog (`config/models.yaml`)
**Status:** Complete
**Files:** `config/models.yaml`, `src/models.py`, `tests/test_config.py`
**Verification:** `pytest tests/test_config.py -v` — 4/4 pass

### T-004: Write response evaluator (`src/evaluator.py`)
**Status:** Complete
**Files:** `src/evaluator.py`, `tests/test_evaluator.py`
**Verification:** `pytest tests/test_evaluator.py -v` — 5/5 pass

### T-005: Write router core (`src/router.py`)
**Status:** Complete
**Files:** `src/router.py`, `tests/test_router.py`
**Verification:** `pytest tests/test_router.py -v` — 5/5 pass

### T-006: Install PyTorch ROCm + vLLM on AMD Jupyter
**Status:** Complete
**Action:** Install torch with ROCm 7.2, verify GPU detection
**Verification:** `python3 -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"` — expects 11

### T-007: Benchmark models on Fireworks
**Status:** Complete
**Action:** Run `uv run python scripts/benchmark.py` with FIREWORKS_API_KEY
**Verification:** Produces benchmark report with token counts and accuracy

### T-008: Run local evaluation
**Status:** Complete
**Action:** Run `uv run python scripts/evaluate.py` after benchmarking
**Verification:** Produces evaluation report JSON

### T-009: Containerize and test Docker
**Status:** Pending
**Action:** `docker build -t amd-router . && docker run amd-router`
**Verification:** Container starts and responds to prompts

### T-010: Submission
**Status:** Pending
**Action:** Complete lablab.ai submission form
**Deadline:** Jul 12, 3:00 PM PT
**Items:** Title, description, video, slides, repo, Docker image

### T-011: Fix evaluator — [ERROR] detection, stronger penalties
**Status:** Complete
**Action:** Penalize [ERROR] responses in evaluator, add stronger code/math penalties
**Verification:** `pytest tests/test_evaluator.py -v` — all pass

### T-012: Add local model health check
**Status:** Complete
**Action:** Router skips vLLM local models gracefully when unavailable
**Verification:** `pytest tests/test_router.py -v` — all pass

### T-013: Add per-category max_tokens
**Status:** Complete
**Action:** factoid=100, math=150, code=1024, reasoning=1024
**Verification:** `pytest tests/ -v` — 17/17 pass

### T-014: Add best=None guard in fallback chain
**Status:** Complete
**Action:** Guard against empty fallback result in router
**Verification:** `pytest tests/test_router.py -v` — all pass

### T-015: Configure GLM 5.2 subagent delegation
**Status:** Complete
**Action:** Configure GLM 5.2 via OpenRouter (Novita ZDR) for complex coding tasks
**Verification:** Subagent config validated

### T-016: Add ruff linter and formatter
**Status:** Complete
**Action:** Install ruff globally, create pyproject.toml, auto-fix 13 lint errors across 7 files
**Verification:** `ruff check src/ tests/ scripts/` — 0 errors

### T-017: Add pre-commit QA pipeline
**Status:** Complete
**Action:** Create scripts/qa.sh (ruff check + format + pytest), .git/hooks/pre-commit hook, `uv run qa` entry point
**Verification:** `bash scripts/qa.sh` — all 3 checks pass (ruff, format, pytest 45/45)

### T-018: Implement task-aware routing
**Status:** Complete
**Action:** Replace tier-based select_model with per-category model mapping (math→gemma-4-9b, code→deepseek, reasoning→glm-5p2, creative→gemma-4-26b)
**Verification:** `pytest tests/test_router.py -v` — 21/21 pass

### T-019: Add test coverage reporting
**Status:** Complete
**Action:** Add pytest-cov to QA pipeline with --cov=src --cov-fail-under=80
**Verification:** `bash scripts/qa.sh` — 37 tests, 84.68% coverage, threshold 80%

### T-020: Deploy Gemma 4 26B on Fireworks dedicated GPU
**Status:** Complete
**Action:** Deploy Gemma 4 26B A4B IT as dedicated endpoint (NVIDIA H200 141GB, $28/h, autoscaling 0-1). Update config/models.yaml with model ID accounts/postboxretinal/deployments/txbj700w. Route 6/9 task categories to Gemma 4 for Gemma Prize eligibility.
**Verification:** `uv run python scripts/evaluate.py` — Gemma 4 handles math, factoid, classification, extraction, summarization, creative, unknown

### T-021: Fix NoneType crash in _call() for null content
**Status:** Complete
**Action:** Add None content check in router._call() to return [ERROR] when API returns content:null. Add TypeError and AttributeError to exception handler.
**Verification:** `pytest tests/ -v` — 37 passed, 84% coverage

### T-022: Fix classify_task() hyphens misclassified as math
**Status:** Complete
**Action:** Remove bare math operators (`+`, `-`, `*`, `/`, `%`) from keyword list in classify_task(). Words like "high-level" or "object-oriented" no longer trigger MATH classification.
**Verification:** Summarization and extraction prompts classified correctly instead of as math

### T-023: Fix evaluator refusal false positives
**Status:** Complete
**Action:** Remove bare "cannot" and "error" from evaluator refusal keywords. Keep specific "i cannot" and "[ERROR]" API check. Code explanations like "it cannot be prime" no longer penalized.
**Verification:** `pytest tests/test_evaluator.py -v` — all pass

### T-024: Increase max_tokens for Gemma 4 reasoning
**Status:** Complete
**Action:** Raise MAX_TOKENS_BY_CATEGORY from 100-512 to 2048-4096. Gemma 4 needs token budget for chain-of-thought reasoning before producing content.
**Verification:** Gemma 4 no longer returns content:null due to token exhaustion

### T-025: Improve evaluate.py CLI output
**Status:** Complete
**Action:** Replace cryptic `[FB]` with clear Status column (PASS/FALLBACK), add live progress per prompt to stderr, add Gemma Prize eligibility footer. Improve token display formatting.
**Verification:** `uv run python scripts/evaluate.py` — shows live progress, Status column, Gemma Prize footer. Final benchmark: 9/14 Gemma, $0.002111, 100% acc.

### T-026: Docker containerization
**Status:** Complete
**Action:** Fix Dockerfile: add config/, tests/, pyproject.toml, uv.lock. Use uv sync --frozen. Add UV_LINK_MODE=copy. Fix entrypoint.sh pipe mode (src.router to src). Verification: `docker run --rm amd-router uv run pytest tests/ -v` — 37 passed.
**Verification:** `docker build -t amd-router . && docker run --rm amd-router uv run pytest tests/ -v`

### T-027: Submission to lablab.ai
**Status:** Pending
**Action:** Submit project with description, tags, and GitHub link to lablab.ai for AMD Hackathon ACT II Track 1.
**Verification:** Submitted before Jul 12 3PM PT deadline
