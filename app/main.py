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
    display_metrics,
    display_model_details,
    display_model_pool,
    display_response,
    task_badge,
)
from src.router import Router  # noqa: E402
from src.tasks import TaskCategory  # noqa: E402

# ---------------------------------------------------------------------------#
#  VERSION
# ---------------------------------------------------------------------------#

try:
    from importlib.metadata import version

    VERSION = version("wayfinder")
except ImportError:
    VERSION = "0.4.0"

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
    st.header("Settings")

    api_key = st.text_input(
        "FIREWORKS_API_KEY",
        type="password",
        key="api_key",
        help="Required for Fireworks AI models",
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
        for i, entry in enumerate(reversed(st.session_state.history)):
            idx = len(st.session_state.history) - i
            with st.container(border=True):
                st.markdown(f"**#{idx}** {entry['prompt'][:60]}...")
                cols = st.columns(4)
                cols[0].metric("Model", entry["model"])
                cols[1].metric("Tokens", entry["tokens"])
                cols[2].metric("Cost", f"${entry['cost']:.6f}")
                cols[3].metric("Time", f"{entry['elapsed']}s")
    else:
        st.caption("No history yet.")

# ---------------------------------------------------------------------------#
#  Main content
# ---------------------------------------------------------------------------#

st.title("Wayfinder")
st.markdown("**Hybrid Token-Efficient Routing Agent** | Task-aware model selection across Gemma 4, DeepSeek V4 Pro, and GLM 5.2. NO-AIslop, straight to the point.")

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
    with st.status("Routing prompt...", expanded=True) as status:
        start = time.time()

        status.update(label="Classifying task...")

        status.update(label="Selecting model...")

        try:
            result = router.route(prompt)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

        # Extract task from router result (single source of truth)
        task_value = result.get("task_category")
        if task_value:
            try:
                task = TaskCategory(task_value)
            except ValueError:
                task = None
        else:
            task = None

        status.update(label="Evaluating response...")
        elapsed = time.time() - start

        status.update(label="Done!", state="complete")

        # Persist to session state
        st.session_state.last_result = result
        st.session_state.last_prompt = prompt
        st.session_state.last_elapsed = elapsed
        st.session_state.last_task = task

        # Add to history
        add_to_history(prompt, result, elapsed)

    if result is not None:
        print(f"[ROUTE] model={result.get('model', '?')}", flush=True)
        st.toast(f"Routed to {result['model']}")

elif submitted and not prompt:
    st.warning("Enter a prompt first.")
    st.stop()

# ---------------------------------------------------------------------------#
#  Display results (from session state so they persist across reruns)
# ---------------------------------------------------------------------------#

result = st.session_state.get("last_result")
elapsed = st.session_state.get("last_elapsed")
task = st.session_state.get("last_task")

if result is not None:
    # Task classification badge
    if task is not None:
        badge = task_badge(task)
        st.markdown(
            f'<div class="task-badge">Task: <strong>{badge}</strong></div>',
            unsafe_allow_html=True,
        )

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
    f"Wayfinder v{VERSION} -- AMD Hackathon ACT II Track 1 -- Hybrid Token-Efficient Routing Agent"
)
