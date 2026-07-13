"""Wayfinder - Hybrid Token-Efficient Routing Agent Web UI (CLI-style)."""

from __future__ import annotations

import os
import sys
import traceback

# Catch-all: log any uncaught exception to crash.log
_log_file = os.path.join(os.path.dirname(__file__), "crash.log")


def _excepthook(typ, val, tb):
    with open(_log_file, "a") as f:
        f.write(f"\n{'=' * 60}\nCRASH at {__import__('datetime').datetime.now()}\n")
        traceback.print_exception(typ, val, tb, file=f)
    traceback.print_exception(typ, val, tb)
    sys.stderr.flush()


sys.excepthook = _excepthook

import time

import streamlit as st

# Must be the first st call
st.set_page_config(
    page_title="Wayfinder",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------#
#  Imports (after set_page_config per Streamlit rules)
# ---------------------------------------------------------------------------#

from app.utils import (  # noqa: E402
    add_to_history,
    display_as_cli,
    display_model_details,
    display_model_pool,
    display_response,
    validate_api_key,
)
from src.models import get_model  # noqa: E402
from src.router import Router  # noqa: E402
from src.tasks import TaskCategory  # noqa: E402

# ---------------------------------------------------------------------------#
#  VERSION
# ---------------------------------------------------------------------------#

from importlib.metadata import version as _pkg_version

try:
    APP_VERSION = _pkg_version("wayfinder")
except Exception:
    APP_VERSION = "debug"

# ---------------------------------------------------------------------------#
#  Session state defaults
# ---------------------------------------------------------------------------#

for key, default in [
    ("history", []),
    ("last_result", None),
    ("last_prompt", ""),
    ("last_elapsed", 0.0),
    ("last_task", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------#
#  Router factory
# ---------------------------------------------------------------------------#


def get_router() -> Router:
    """Build a fresh Router so it picks up the current FIREWORKS_API_KEY."""
    return Router()


# ---------------------------------------------------------------------------#
#  Sidebar
# ---------------------------------------------------------------------------#

with st.sidebar:
    st.markdown("**Wayfinder**")

    # API Key with colored border based on validation state
    # Force reset validation on every rerun if no api_key is stored
    if "api_key" in st.session_state and not st.session_state.api_key:
        st.session_state.api_key_validated = None

    key_valid = st.session_state.get("api_key_validated")
    if key_valid is True:
        border_color = "green"
    elif key_valid is False:
        border_color = "red"
    else:
        border_color = "#333"

    api_key_locked = key_valid == True
    api_key = st.text_input(
        "FIREWORKS_API_KEY",
        type="password",
        key="api_key",
        disabled=api_key_locked,
        help="Required for Fireworks AI models",
    )

    # Validate API key (only when a key is present and not yet validated)
    if api_key and st.session_state.get("api_key_validated") is None:
        with st.spinner("Validating API key..."):
            is_valid = validate_api_key(api_key)
            st.session_state.api_key_validated = is_valid

    is_valid = st.session_state.get("api_key_validated")
    if is_valid is True:
        st.markdown(
            "<span style='color:#00D4AA;font-size:0.75em'>API key valid</span>",
            unsafe_allow_html=True,
        )
        if st.button("Change key", key="change_key"):
            st.session_state.api_key_validated = None
            st.rerun()
    elif is_valid is False:
        st.markdown(
            "<span style='color:#FF4444;font-size:0.75em'>✗ API key invalid</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Model Pool with live data
    if api_key:
        router = get_router()
        display_model_pool(router, api_key)

    st.divider()

    # History panel
    st.markdown("**History**")
    if st.session_state.history:
        # Model color mapping for history dots
        MODEL_COLORS = {
            "deepseek": "#00D4AA",
            "glm": "#3D9DF3",
            "gemma": "#FFBF00",
        }

        def _model_color(model: str) -> str:
            for key, color in MODEL_COLORS.items():
                if key in model.lower():
                    return color
            return "#888"

        for i, entry in enumerate(reversed(st.session_state.history)):
            idx = len(st.session_state.history) - i
            prompt_preview = (
                entry["prompt"][:40] + "..." if len(entry["prompt"]) > 40 else entry["prompt"]
            )
            ts = entry.get("timestamp", "")
            time_only = ts.split(" ")[1][:5] if ts and " " in ts else ""
            model = entry.get("model", "?")
            try:
                mm = get_model(model)
                model_display = mm.display_name
            except ValueError:
                model_display = model
            dot_color = _model_color(model)

            # Colored dot for visual model distinction
            st.markdown(
                f"<span style='color:{dot_color}'>●</span> "
                f"#{idx} {prompt_preview} — **{model_display}** `{time_only}`",
                unsafe_allow_html=True,
            )

            if st.button(f"Load #{idx}", key=f"hist_{idx}", use_container_width=True):
                # Restore this history entry into the main display
                st.session_state.last_result = {
                    "model": model,
                    "tokens": entry["tokens"],
                    "cost": entry["cost"],
                    "accuracy_score": entry["accuracy"],
                    "fallback_used": False,
                    "response": entry.get("full_response", "[restored from history]"),
                    "task_category": entry.get("task_category"),
                }
                st.session_state.last_prompt = entry["prompt"]
                st.session_state.last_elapsed = entry["elapsed"]
                st.rerun()
    else:
        st.caption("No history yet.")

# ---------------------------------------------------------------------------#
#  Main content
# ---------------------------------------------------------------------------#

st.title("Wayfinder")
st.markdown(
    "**Hybrid Token-Efficient Routing Agent** | Task-aware model selection across Gemma 4, DeepSeek V4 Pro, and GLM 5.2. NO-AIslop, straight to the point."
)

# Apply dynamic theme
st.markdown(
    """
<style>
.cli-card {
    background-color: var(--st-secondary-background-color);
    border: 1px solid var(--st-border-color, #ddd);
    border-radius: 0.5rem;
    padding: 1rem;
    font-family: var(--st-font-family-mono, monospace);
}
.task-badge { font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

if not api_key:
    st.warning("Enter your Fireworks API key in the sidebar to start routing.")
    st.stop()

os.environ["FIREWORKS_API_KEY"] = api_key

# ---------------------------------------------------------------------------#
#  Prompt input
# ---------------------------------------------------------------------------#

with st.form("route_form"):
    prompt = st.text_area(
        "Enter your prompt",
        placeholder="e.g., What is the capital of Japan?",
    )
    submitted = st.form_submit_button("Route", use_container_width=True)

# ---------------------------------------------------------------------------#
#  Routing logic
# ---------------------------------------------------------------------------#

router = get_router()
result = None
elapsed = 0.0
submit_triggered = submitted and prompt

if submit_triggered:
    progress_bar = st.progress(0, text="Classifying task...")

    start = time.time()

    progress_bar.progress(20, text="Classifying task...")

    progress_bar.progress(40, text="Selecting model...")

    try:
        result = router.route(prompt)
    except Exception as e:
        progress_bar.empty()
        st.error(f"Error: {e}")
        st.stop()

    progress_bar.progress(80, text="Evaluating response...")
    elapsed = time.time() - start

    # Extract task category
    task_value = result.get("task_category")
    if task_value:
        try:
            task = TaskCategory(task_value)
        except ValueError:
            task = None
    else:
        task = None

    progress_bar.progress(100, text="Done!")
    # Remove the progress bar after 0.5s (it will be gone on next rerun anyway)

    # Persist to session state
    st.session_state.last_result = result
    st.session_state.last_prompt = prompt
    st.session_state.last_elapsed = elapsed
    st.session_state.last_task = task
    # Store full response for history restore
    add_to_history(prompt, {**result, "full_response": result.get("response", "")}, elapsed)

    if result is not None:
        try:
            mm = get_model(result["model"])
            model_disp = mm.display_name
        except ValueError:
            model_disp = result["model"]
        st.toast(f"Routed to {model_disp}")

elif submitted and not prompt:
    st.warning("Enter a prompt first.")
    st.stop()

# ---------------------------------------------------------------------------#
#  Display results (from session state so they persist across reruns)
# ---------------------------------------------------------------------------#

result = st.session_state.get("last_result")
elapsed = st.session_state.get("last_elapsed", 0.0)

if result is not None:
    st.divider()

    # CLI-style output card
    st.markdown("**CLI Output**")
    display_as_cli(result, elapsed)

    st.divider()

    # Response in code block
    display_response(result["response"])

    # Model details expander
    display_model_details(result)

# ---------------------------------------------------------------------------#
#  Footer
# ---------------------------------------------------------------------------#

st.divider()
st.caption(
    f"Wayfinder v{APP_VERSION} -- AMD Hackathon ACT II Track 1 -- Hybrid Token-Efficient Routing Agent"
)

# Auto-refresh history when new entries appear
if "history" in st.session_state:
    current_count = len(st.session_state.history)
    if "history_count" not in st.session_state:
        st.session_state.history_count = current_count
    elif st.session_state.history_count != current_count:
        st.session_state.history_count = current_count
        st.rerun()
