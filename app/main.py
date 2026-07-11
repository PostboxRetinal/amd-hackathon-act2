"""Wayfinder - Hybrid Token-Efficient Routing Agent Web UI (CLI-style)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Read version from package metadata (SEMVER)
_VERSIONS = {"wayfinder": "0.2.0"}
try:
    from importlib.metadata import version as _pkg_ver
    _VERSIONS["wayfinder"] = _pkg_ver("wayfinder")
except Exception:
    pass
VERSION = _VERSIONS.get("wayfinder", "0.2.0")

from src.router import Router
from src.tasks import TaskCategory, classify_task

from app.utils import (
    add_to_history,
    display_as_cli,
    display_metrics,
    display_model_details,
    display_model_pool,
    display_response,
    task_badge,
)

# ---------------------------------------------------------------------------#
#  Page config
# ---------------------------------------------------------------------------#

st.set_page_config(
    page_title="Wayfinder",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------#
#  Session state init
# ---------------------------------------------------------------------------#

if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""
if "last_elapsed" not in st.session_state:
    st.session_state.last_elapsed = 0.0
if "last_task" not in st.session_state:
    st.session_state.last_task = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ---------------------------------------------------------------------------#
#  Router instantiation
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
        help="Required for Fireworks AI models",
    )

    st.session_state.dark_mode = st.toggle(
        "Dark mode",
        value=st.session_state.dark_mode,
        help="Toggle dark/light theme styling",
    )

    st.divider()

    # Model pool
    if api_key:
        router = get_router()
        display_model_pool(router, api_key)

    st.divider()

    # Query history
    st.subheader("Query History")
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history)):
            idx = len(st.session_state.history) - i
            label = entry["prompt"][:60]
            if len(entry["prompt"]) > 60:
                label += "..."
            with st.expander(f"#{idx} [{entry['timestamp']}] {label}", expanded=False):
                r = entry["result"]
                st.markdown(f"**Model:** {r['model']}")
                st.markdown(f"**Accuracy:** {r['accuracy_score']:.2f}")
                st.markdown(f"**Tokens:** {r['tokens']}")
                st.markdown(f"**Cost:** ${r['cost']:.6f}")
                st.markdown(f"**Fallback:** {'Yes' if r['fallback_used'] else 'No'}")
                st.markdown(f"**Time:** {entry['elapsed']:.1f}s")
                st.caption(entry["prompt"])
    else:
        st.caption("No queries yet.")

    st.divider()
    st.caption(
        "Wayfinder distributes prompts across 3 model tiers "
        "based on task category. Built with Python, uv, and Fireworks AI."
    )

# ---------------------------------------------------------------------------#
#  Dark / light mode CSS
# ---------------------------------------------------------------------------#

if st.session_state.dark_mode:
    bg_color = "#0e1117"
    text_color = "#fafafa"
    card_bg = "#1a1a2e"
    border_color = "#33334d"
else:
    bg_color = "#ffffff"
    text_color = "#1a1a2e"
    card_bg = "#f0f2f6"
    border_color = "#d0d0e0"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .cli-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }}
    .task-badge {{
        display: inline-block;
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 14px;
        margin: 4px 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------#
#  Header
# ---------------------------------------------------------------------------#

st.title("Wayfinder")
st.markdown(
    "**Hybrid Token-Efficient Routing Agent** -- Task-aware model selection "
    "across Gemma 4, DeepSeek V4 Pro, and GLM 5.2."
)

# ---------------------------------------------------------------------------#
#  API key check
# ---------------------------------------------------------------------------#

if not api_key:
    st.warning("Enter your Fireworks API key in the sidebar to start routing.")
    st.stop()

os.environ["FIREWORKS_API_KEY"] = api_key

# ---------------------------------------------------------------------------#
#  Prompt input
# ---------------------------------------------------------------------------#

prompt = st.text_area(
    "Enter your prompt",
    placeholder="e.g., What is the capital of Japan?",
    height=100,
    key="prompt_input",
)

st.caption("Tip: Press Ctrl+Enter (Cmd+Enter on Mac) to submit.")

col1, col2, col3 = st.columns([1, 1, 5])
with col1:
    routed = st.button("Route", type="primary", use_container_width=True)
with col2:
    route_again = st.button(
        "Route Again",
        use_container_width=True,
        disabled=st.session_state.last_result is None,
        help="Re-run the last prompt",
    )
with col3:
    pass

# Ctrl+Enter handling: Streamlit text_area submits on Ctrl+Enter by default
# when using the key parameter. We detect submit via button or session state.

submit_triggered = routed or route_again

# If "Route Again" is clicked, use the last prompt
if route_again and st.session_state.last_prompt:
    prompt = st.session_state.last_prompt

# ---------------------------------------------------------------------------#
#  Router instantiation (re-declared for routing section)
# ---------------------------------------------------------------------------#


def get_router() -> Router:
    """Build a fresh Router so it picks up the current FIREWORKS_API_KEY."""
    return Router()


# ---------------------------------------------------------------------------#
#  Routing logic
# ---------------------------------------------------------------------------#

if submit_triggered and prompt:
    start = time.time()
    try:
        with st.status("Routing prompt...", expanded=True) as status:
            status.update(label="Classifying task...")
            task = classify_task(prompt)

            status.update(label=f"Selecting model for {task.value}...")
            router = get_router()

            status.update(label="Routing through model chain...")
            result = router.route(prompt)

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

        st.toast(f"Routed to {result['model']}")

    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

elif submit_triggered and not prompt:
    st.warning("Enter a prompt first.")
    st.stop()

# ---------------------------------------------------------------------------#
#  Display results (from session state so they persist across reruns)
# ---------------------------------------------------------------------------#

result = st.session_state.last_result
elapsed = st.session_state.last_elapsed
task = st.session_state.last_task

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
    st.markdown('<div class="cli-card">', unsafe_allow_html=True)
    display_as_cli(result, elapsed)
    st.markdown("</div>", unsafe_allow_html=True)

    # Metrics row
    display_metrics(result, elapsed)

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
    f"Wayfinder v{VERSION} -- AMD Hackathon ACT II Track 1 -- "
    "Gemma Prize eligible (requires active Gemma 4 deploy or local llama.cpp server)"
)
