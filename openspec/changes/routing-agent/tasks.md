# Routing Agent — Tasks

## Task List

### T-001: Setup project structure
**Status:** ✅ Complete
**Files:** `.gitignore`, `Dockerfile`, `entrypoint.sh`, `requirements.txt`, `config/models.yaml`
**Verification:** `git status` shows tracked files

### T-002: Write task classifier (`src/tasks.py`)
**Status:** ✅ Complete
**Files:** `src/tasks.py`, `tests/test_tasks.py`
**Verification:** `pytest tests/test_tasks.py -v` — 6/6 pass

### T-003: Write model catalog (`config/models.yaml`)
**Status:** ✅ Complete
**Files:** `config/models.yaml`, `src/models.py`, `tests/test_config.py`
**Verification:** `pytest tests/test_config.py -v` — 4/4 pass

### T-004: Write response evaluator (`src/evaluator.py`)
**Status:** ✅ Complete
**Files:** `src/evaluator.py`, `tests/test_evaluator.py`
**Verification:** `pytest tests/test_evaluator.py -v` — 5/5 pass

### T-005: Write router core (`src/router.py`)
**Status:** ✅ Complete
**Files:** `src/router.py`, `tests/test_router.py`
**Verification:** `pytest tests/test_router.py -v` — 5/5 pass

### T-006: Install PyTorch ROCm + vLLM on AMD Jupyter
**Status:** 🔄 In Progress
**Action:** Install torch with ROCm 7.2, verify GPU detection
**Verification:** `python3 -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"` — expects 11

### T-007: Benchmark models on Fireworks
**Status:** ⏳ Pending
**Action:** Run `uv run python scripts/benchmark.py` with FIREWORKS_API_KEY
**Verification:** Produces benchmark report with token counts and accuracy

### T-008: Run local evaluation
**Status:** ⏳ Pending
**Action:** Run `uv run python scripts/evaluate.py` after benchmarking
**Verification:** Produces evaluation report JSON

### T-009: Containerize and test Docker
**Status:** ⏳ Pending
**Action:** `docker build -t amd-router . && docker run amd-router`
**Verification:** Container starts and responds to prompts

### T-010: Submission
**Status:** ⏳ Pending
**Action:** Complete lablab.ai submission form
**Deadline:** Jul 11, 11:00 AM COT
**Items:** Title, description, video, slides, repo, Docker image
