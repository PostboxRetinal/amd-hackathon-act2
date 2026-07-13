# Routing Agent — Tasks

**Version:** v0.5.6b

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
**Status:** Complete
**Action:** `podman build -t amd-router . && podman run amd-router`
**Verification:** Container builds and runs tests successfully. Includes entrypoint passthrough, .dockerignore, Streamlit Dockerfile.web.

### T-010: Submission
**Status:** Complete
**Action:** Complete lablab.ai submission form
**Deadline:** Jul 12, 3:00 PM PT
**Items:** Title, description, video, slides, repo, Docker image
**Verification:** Submission form completed with all required items (Title, description, video, slides, repo, Docker image)

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

### T-026: Frontend Streamlit routing interface
**Status:** Complete
**Action:** Create interactive Streamlit frontend for Wayfinder with prompt input, model selection display, routing history, and CLI-style output.
**Files:** `app/main.py`, `app/utils.py`
**Verification:** `streamlit run app/main.py` launches web UI at localhost:8501.

### T-027: Submission to lablab.ai
**Status:** Complete
**Action:** Submit project with description, tags, and GitHub link to lablab.ai for AMD Hackathon ACT II Track 1.
**Verification:** Submitted before Jul 12 3PM PT deadline

### T-028: Purge gemma-4-9b, migrate tests to STANDARD tier
**Status:** Complete
**Action:** Remove gemma-4-9b (model never existed on Fireworks). Migrate all test references from FAST tier to STANDARD. Update config/models.yaml and router.
**Verification:** `pytest tests/ -v` — 46 passed, no FAST references remain

### T-029: Descriptive error messages in _call()
**Status:** Complete
**Action:** Replace generic `[ERROR]` with descriptive messages: missing API key, timeout, connection refused, parse errors, API errors. Include model URL context for local models.
**Verification:** `curl without API key` → `[ERROR: FIREWORKS_API_KEY not set...]` instead of `[ERROR]`

### T-030: Streamlit frontend (Wayfinder Web UI)
**Status:** Complete
**Action:** Build complete Streamlit web interface in app/ directory. CLI-style output, live routing status with st.status(), st.toast() notifications, @st.cache_data for Router, dark mode, query history, Ctrl+Enter shortcut. Dockerfile.web for containerized deployment.
**Verification:** `uv run streamlit run app/main.py` — launches without error, all features functional

### T-031: Evaluator [ERROR: prefix detection
**Status:** Complete
**Action:** Change evaluator from exact `"[ERROR]"` match to `startswith("[ERROR")`. All new descriptive error messages are properly caught and scored 0.0.
**Verification:** `pytest tests/test_evaluator.py -v` — all pass

### T-032: Model pool + Refresh from Fireworks
**Status:** Superseded by T-052/T-054
**Action:** Add sidebar Model Pool showing all configured models with status (Ready/Paused/Down) and pricing. Add Refresh button that fetches live pricing from Fireworks API for Wayfinder's models only.
**Verification:** Streamlit sidebar shows model list + Refresh button fetches live data

### T-033: Code review fixes (6 items)
**Status:** Complete
**Action:** `_is_local_model()` accepts both `vllm` and `local`. `best is None` path includes `"model"` key. Cost uses actual API token count. `.dockerignore` created. README updated with Model Requirements section. Empty dead files removed.
**Verification:** `pytest tests/ -v --cov=src` — 46 passed, 86% coverage

### T-034: SEMVER + dynamic versioning
**Status:** Complete
**Action:** Bump version 0.1.0 → 0.2.0 per SEMVER (minor: new frontend feature). Read version dynamically via importlib.metadata. Add .streamlit/config.toml to disable telemetry.
**Verification:** `streamlit run` footer shows `Wayfinder v0.2.0`

### T-035: Coverage bump — 51 tests, 87% coverage
**Status:** Complete
**Action:** Add 5 targeted tests for cache hit, route result keys, empty prompt, long prompt, and model key presence. Router coverage at 87% (7% above 80% threshold).
**Verification:** `pytest tests/ -v --cov=src` — 51 passed, 87.40% coverage

### T-036: Cache hit + route edge case tests
**Status:** Complete
**Action:** Add tests: cache hit returns same result, cache does not increment stats, route result contains all required keys, empty prompt returns valid dict, long prompt (400+ chars) routes correctly.
**Verification:** `pytest tests/test_router.py -v` — all 28 test methods pass

### T-037: Model Pool redesign with live Refresh
**Status:** Superseded by T-052/T-054
**Action:** Rework display_model_pool() to merge static config data with live data from Fireworks API stored in st.session_state.live_models. Replace separate display_fireworks_pool() block with inline live data in each model row. On Refresh click, store API response in session state and call st.rerun().
**Verification:** Refresh button updates pricing and context values directly in the pool rows, not in a separate block.

### T-038: Status labels: UP/DOWN/NEEDS_SETUP
**Status:** Complete
**Action:** Replace generic "Ready"/"Paused"/"Down" labels with descriptive statuses: UP for serverless models, NEEDS_SETUP for Gemma 4 dedicated deploys (require dashboard activation), DOWN for unreachable local servers.
**Files:** `app/utils.py`

### T-039: Version bump 0.2.0 -> 0.3.0
**Status:** Complete
**Action:** Increment MINOR version in pyproject.toml per SEMVER for the live refresh and status redesign features.
**Verification:** `streamlit run` footer shows `Wayfinder v0.3.0`

### T-040: Model pool table display with st.dataframe
**Status:** Superseded by T-052/T-054
**Action:** Replace per-row st.markdown() model pool with st.dataframe() using pandas + column_config for sortable columns. Keep Refresh button and timestamp below table.
**Files:** `app/utils.py`
**Verification:** Model pool renders as interactive sortable table in sidebar. Refresh still works.

### T-041: Live model status from Fireworks API response
**Status:** Complete
**Action:** Replace hardcoded status logic (UP/SETUP/DOWN based on model name) with real data from Fireworks API /v1/models endpoint. Models present in API response = UP, models absent = SETUP, local models = DOWN. Update fetch_fireworks_models() to return available_ids alongside pricing.
**Files:** `app/utils.py`
**Verification:** Model Pool statuses reflect actual Fireworks API data after clicking Refresh. Serverless models show UP, paused deploys show SETUP.

### T-042: Version bump 0.3.0 -> 0.4.0
**Status:** Complete
**Action:** Increment MINOR version for live API status feature.
**Verification:** `streamlit run` footer shows `Wayfinder v0.4.0`

### T-043: Streamlit UI improvements (fragments, forms, layout)
**Status:** Complete
**Action:** Apply validated Streamlit 1.59 patterns:
- Wrap Model Pool in `@st.fragment` for independent rerun on Refresh
- Wrap prompt + Route in `st.form()` to prevent sidebar reruns while typing
- Add `layout="wide"` to `st.set_page_config`
- Add `st.container(height=...)` for consistent history area height
- (Optional) Material icons via `:material/icon:` for headers
**Files:** `app/main.py`, `app/utils.py`
**Verification:** No visual regressions. Refresh only reruns Model Pool fragment. Typing in prompt doesn't rerun sidebar. `pytest` still passes.

### T-044: Validate against public sample tasks
**Status:** Complete
**Action:** Run all 10 AMD Hackathon sample tasks through Wayfinder router. Verify correctness, format, and fallback behavior against official judging criteria. Report accuracy and cost.
**Files:** `tests/test_benchmark.py`
**Verification:** All 10 tasks pass with expected output format.

### T-045: Increase FACTOID max_tokens
**Status:** Complete
**Action:** Increase FACTOID max_tokens from 2048 to 4096 for detailed factual answers.
**Files:** `src/router.py`
**Change:** `TaskCategory.FACTOID: 4096`

### T-046: Add format validation for summarization
**Status:** Complete
**Action:** Add evaluator checks for exact sentence count (T04) and bullet count/word length (T04b) compliance.
**Files:** `src/evaluator.py`
**Verification:** Summarization tasks enforce exact output format per judging requirements.

### T-047: Gemma Prize eligibility documentation
**Status:** Complete
**Action:** Verify local llama.cpp server is running for demo. Document Gemma Prize eligibility requirements in README.
**Files:** `README.md`
**Verification:** `curl localhost:8000/v1/models` returns 200. README mentions local Gemma 4 setup.

### T-048: Pre-submission Docker validation
**Status:** Complete
**Action:** Verify Docker image builds, runs without local files, and produces correct output. Check: public registry, entrypoint, no hardcoded secrets.
**Files:** `Dockerfile`, `entrypoint.sh`
**Verification:** `podman run wayfinder "test"` returns valid response in < 30s.

### T-049: Output format compliance
**Status:** Complete
**Action:** Validate JSON output structure matches judging spec. Ensure required fields present, valid JSON, task IDs preserved.
**Files:** `src/cli.py` or `src/__main__.py`
**Verification:** CLI output is valid JSON array with required fields.

### T-050: Clean machine test
**Status:** Complete
**Action:** Document exact steps to run from a clean machine. Verify no local dependencies, no manual setup, no private secrets required.
**Files:** `README.md`
**Verification:** Fresh Ubuntu + Docker can run `docker run wayfinder <prompt>` without errors.

### T-051: Final validation and documentation sync
**Status:** Complete
**Action:** Sync OpenSpec SDD and README to final project state. Confirm 73 tests, 82% coverage (threshold 75%), all T-001..T-050 Complete. evaluator.py 55% (untested check_* functions), models.py 100%, router.py 86%, tasks.py 90%. Docker ready, --json output, GUI/CLI aligned. Validate OpenSpec change and specs.
**Verification:** `npx openspec validate routing-agent --type change` and `--specs` both pass; README badges show 73 tests / 82% coverage; T-001..T-051 all Complete.

### T-052: UI Overhaul: Sidebar restructuring
**Status:** Complete
**Action:** Moved API key, Model Pool, History to st.sidebar
**Verification:** Sidebar contains API key input, Model Pool, and History controls

### T-053: UI Overhaul: Mini status bar
**Status:** Complete
**Action:** Replaced st.status() spinner with compact inline bar
**Verification:** Routing status renders as compact inline bar, no spinner

### T-054: UI Overhaul: Model Pool cards
**Status:** Complete
**Action:** Replaced dataframe with colored status cards
**Verification:** Model Pool renders as colored status cards in sidebar

### T-055: UI Overhaul: History list
**Status:** Complete
**Action:** Replaced bordered containers with compact single-line entries
**Verification:** History renders as compact single-line entries

### T-056: UI Overhaul: Response terminal
**Status:** Complete
**Action:** Response styled as bordered terminal block
**Verification:** Response area renders as bordered terminal block

### T-057: Version bump
**Status:** Complete
**Action:** Updated SEMVER from 0.4.0 to 0.5.0
**Verification:** `streamlit run` footer shows `Wayfinder v0.5.0`

### T-058: Sidebar: model grouping
**Status:** Complete
**Action:** Models split into Serverless and Deployments sections with category labels
**Verification:** Sidebar shows Serverless and Deployments sections with category labels

### T-059: Live deployment status
**Status:** Complete
**Action:** fetch_deployment_status() API, live state/replicas in tooltips
**Verification:** Deployment status reflects live state/replicas in tooltips

### T-060: Dynamic history auto-refresh
**Status:** Complete
**Action:** Added auto-refresh when new history entries appear via st.rerun() count tracking
**Verification:** History updates instantly when new entries are added

### T-061: Interactive clickable history
**Status:** Complete
**Action:** History entries are now clickable buttons that restore the full routing result into the main display
**Verification:** Clicking a history entry loads model, response, accuracy, and task badge

### T-062: Model-based history coloring
**Status:** Complete
**Action:** History entries colored by model: cyan for DeepSeek, blue for GLM, amber for Gemma
**Verification:** Each history entry shows a colored dot matching its model

### T-063: Full Fireworks API path display
**Status:** Complete
**Action:** Model cards now show the full Fireworks API path (e.g. accounts/fireworks/models/glm-5p2) under the model name
**Verification:** Each model card shows its Fireworks path in gray monospace

### T-064: Human-readable model display names
**Status:** Complete
**Action:** Added MODEL_DISPLAY_NAMES mapping with readable names (Gemma 4 31B IT, DeepSeek V4 Pro, GLM 5.2, etc.)
**Verification:** All model references display human-readable names instead of raw API names

### T-065: Live pricing and context from API
**Status:** Complete
**Action:** Refresh button now fetches live pricing and context length from Fireworks API, falls back to static config when unavailable. Data source shown in hover tooltip.
**Verification:** After clicking Refresh, model prices and context reflect API values; tooltip shows "Data: live" or "Data: static"

### T-066: Model pool UI polish
**Status:** Complete
**Action:** Added colored dot per model (distinct blues per Gemma, purple for DeepSeek, white for GLM, teal for NVFP4), model card links to Fireworks, LIVE badge for serverless, deployment creation link, removed redundant labels
**Files:** app/utils.py
**Verification:** Sidebar shows polished model cards with colors, links, LIVE badge when data is fresh

### T-067: OpenSpec update
**Status:** Complete
**Action:** Added T-060 through T-067 documenting all recent changes
**Verification:** OpenSpec validates successfully

### T-068: Python 3.11 minimum
**Status:** Complete
**Action:** Bumped requires-python from >=3.10 to >=3.11 for tomllib stdlib support
**Files:** pyproject.toml

### T-069: tomllib version reading
**Status:** Complete
**Action:** Replaced importlib.metadata.version() with tomllib to read version directly from pyproject.toml, avoiding PEP 440 normalization
**Files:** app/main.py, src/__main__.py

### T-070: python-pptx moved to dev dependencies
**Status:** Complete
**Action:** Moved python-pptx from core dependencies to dev dependency group (only needed for slide generation)
**Files:** pyproject.toml

### T-071: Sidebar link icons removed
**Status:** Complete
**Action:** Removed ↗ link icons from model name display in sidebar cards. model_id shown as plain text.
**Files:** app/utils.py

### T-072: Version bump 0.5.0 → 0.5.6b
**Status:** Complete
**Action:** Updated version in pyproject.toml
**Files:** pyproject.toml

### T-073: Remove invented ModelTier field
**Status:** Complete
**Action:** Removed tier (cheap/standard/premium) from config/models.yaml and all code references. Replaced `_pick(tier)` with `_pick_first()` in router. Deleted ModelTier enum from models.py. Removed tier display from UI.
**Files:** config/models.yaml, src/models.py, src/router.py, app/utils.py, tests/test_config.py, tests/test_router.py

### T-074: CLI output card + Response syntax highlighting
**Status:** Complete
**Action:** Replaced `st.markdown()` metric labels with native `st.metric()`. Removed `<br>` hack. Added conditional `st.warning()` for fallback. Auto-detects response language (Python, SQL, Bash, JSON, text) for syntax highlighting in `st.code()`.
**Files:** app/utils.py

### T-075: Test coverage to 88% (73 tests)
**Status:** Complete
**Action:** Rewrote test_router.py with 46 tests covering all 8 task categories, fallback chain ordering, error paths (bad JSON, timeout, OSError), cache hit/miss, and CLI main(). Rewrote test_evaluator.py with 22 tests covering all check_* AMD compliance helpers and all TaskCategory branches. Total: 73 tests, 88% coverage.
**Files:** tests/test_router.py, tests/test_evaluator.py

### T-076: Full QA pipeline green
**Status:** Complete
**Action:** ruff check PASS, ruff format PASS (18 files), pytest 73/73 PASS, coverage 88% (threshold 75%). All gates green.
**Files:** tests/
