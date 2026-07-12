"""Shared helpers for Wayfinder UI."""

from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit.column_config import TextColumn

from src.models import get_model
from src.router import Router
from src.tasks import TaskCategory


def _on_refresh(fw_key: str) -> None:
    """Refresh callback: fetch live model data from Fireworks API."""
    try:
        data = fetch_fireworks_models(fw_key)
        if data is not None:
            st.session_state.live_models = data
            st.session_state.live_updated = datetime.now().strftime("%H:%M")
            st.session_state.pop("live_error", None)
        else:
            st.session_state.live_error = "API call failed or returned empty"
    except Exception:
        import traceback

        traceback.print_exc()
        st.session_state.live_error = "Refresh failed - check API key or network"


# Bracket-style task markers for badge display.
_TASK_META: dict[TaskCategory, tuple[str, str]] = {
    TaskCategory.MATH: ("[MATH]", "Math"),
    TaskCategory.CODE: ("[CODE]", "Code"),
    TaskCategory.REASONING: ("[BRAIN]", "Reasoning"),
    TaskCategory.FACTOID: ("[FACT]", "Factoid"),
    TaskCategory.CREATIVE: ("[WAND]", "Creative"),
    TaskCategory.CLASSIFICATION: ("[TAG]", "Classification"),
    TaskCategory.SUMMARIZATION: ("[DOC]", "Summarization"),
    TaskCategory.EXTRACTION: ("[EXTRACT]", "Extraction"),
    TaskCategory.UNKNOWN: ("[?]", "Unknown"),
}


def task_badge(task: TaskCategory) -> str:
    """Return a marker + label string for the task category."""
    marker, label = _TASK_META.get(task, _TASK_META[TaskCategory.UNKNOWN])
    return f"{marker} {label}"


def display_as_cli(result: dict, elapsed: float) -> None:
    """Render result summary as a polished output card."""
    model = result.get("model", "?")
    acc = float(result.get("accuracy_score", 0.0))
    tokens = result.get("tokens", 0)
    cost = float(result.get("cost", 0.0))
    fb = bool(result.get("fallback_used", False))

    status_color = "red" if fb else "green"
    acc_color = "green" if acc >= 0.7 else ("orange" if acc >= 0.4 else "red")
    acc_str = f":{acc_color}[{acc:.2f}]"

    task = st.session_state.get("last_task")
    task_str = task_badge(task) if task is not None else task_badge(TaskCategory.UNKNOWN)

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1])
        head_l.markdown(
            f"<span style='color:{status_color}'>●</span> **{model}**",
            unsafe_allow_html=True,
        )
        head_r.markdown(f"Task: {task_str}")

        st.divider()

        m1, m2, m3 = st.columns(3)
        m1.markdown("**Response Time**")
        m2.markdown("**Tokens**")
        m3.markdown("**Cost**")
        st.markdown("<br>", unsafe_allow_html=True)
        m1.markdown(f"{elapsed:.1f}s")
        m2.markdown(f"{tokens:,}")
        m3.markdown(f"${cost:.6f}")

        st.divider()

        st.markdown(
            f"**Accuracy:** {acc_str}  ·  **Fallback:** {'yes' if fb else 'no'}"
        )
        st.caption(f"Completed in {elapsed:.1f}s")


def display_metrics(result: dict, elapsed: float) -> None:
    """Show key metrics in columns below the CLI block."""
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        st.metric("Model", result["model"])
    with col_b:
        st.metric("Accuracy", f"{result['accuracy_score']:.2f}")
    with col_c:
        st.metric("Tokens", result["tokens"])
    with col_d:
        st.metric("Cost", f"${result['cost']:.6f}")
    with col_e:
        st.metric("Time", f"{elapsed:.1f}s")


def display_response(response: str) -> None:
    """Show the full model response in a terminal-style block."""
    st.markdown("**Response**")
    with st.container(border=True):
        st.code(response, language="text", line_numbers=False)


def display_model_details(result: dict) -> None:
    """Show model details in an expander."""
    with st.expander("Model Details"):
        try:
            model = get_model(result["model"])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Name:** {model.name}")
                st.markdown(f"**Tier:** {model.tier.value}")
                st.markdown(f"**Provider:** {model.provider}")
            with col2:
                st.markdown(f"**Cost / 1K tokens:** ${model.cost_per_1k_tokens}")
                st.markdown(f"**Accuracy score:** {model.accuracy_score}")
                st.markdown(f"**Context limit:** {model.context_limit:,}")
        except ValueError:
            st.markdown(f"Model `{result['model']}` not found in catalog.")


def display_status_bar(model: str, elapsed: float, tokens: int, cost: float) -> None:
    """Show a compact status bar after routing completes."""
    st.markdown(
        f"**Done!** `{model}` | {elapsed:.1f}s | {tokens:,} tokens | ${cost:.6f}"
    )
    st.divider()


def fetch_fireworks_models(api_key: str) -> dict | None:
    """Fetch pricing for Wayfinder's models from Fireworks AI API.

    Returns a dict with 'pricing' (keyed by model name) and
    'available_ids' (list of expected model IDs found in the API response),
    filtered to only the models we use in routing.
    """

    wayfinder_models = {
        "deepseek-v4-pro": "accounts/fireworks/models/deepseek-v4-pro",
        "glm-5p2": "accounts/fireworks/models/glm-5p2",
        "gemma-4-26b": "accounts/postboxretinal/deployments/txbj700w",
        "gemma-4-31b": "accounts/fireworks/models/gemma-4-31b-it",
    }

    req = urllib.request.Request(
        "https://api.fireworks.ai/inference/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode())
            data = raw if isinstance(raw, list) else raw.get("data", [])
    except Exception:
        return None

    result = {"pricing": {}, "available_ids": []}
    for m in data:
        mid = m.get("id", "")
        for name, expected_id in wayfinder_models.items():
            if mid == expected_id or name in mid:
                cost = m.get("pricing", {})
                result["pricing"][name] = {
                    "id": mid,
                    "display_name": m.get("display_name", name),
                    "prompt_cost": cost.get("prompt", 0),
                    "completion_cost": cost.get("completion", 0),
                    "context_length": m.get("context_length", 0),
                }
                result["available_ids"].append(expected_id)
                break
    return result


def display_model_pool(router: Router, api_key: str | None = None) -> None:
    """Show model pool as compact status cards with colors."""
    if "live_models" not in st.session_state:
        st.session_state.live_models = {}
    if "live_updated" not in st.session_state:
        st.session_state.live_updated = None

    all_models = router._all()
    effective_key = api_key or os.environ.get("FIREWORKS_API_KEY")
    live = st.session_state.get("live_models", {})
    live_pricing = live.get("pricing", {})
    available_ids = live.get("available_ids", set())

    for m in all_models:
        # Determine status
        if "gemma" in m.name.lower():
            status = "SETUP"
            status_color = "orange"
        elif m.provider == "local":
            status = "DOWN"
            status_color = "red"
        elif live_pricing:
            status = "UP" if m.model_id in available_ids else "SETUP"
            status_color = "green" if status == "UP" else "orange"
        else:
            status = "UP" if "deployments" not in m.model_id else "SETUP"
            status_color = "green" if status == "UP" else "orange"

        if m.provider == "local":
            tier_label = "local"
        else:
            tier_label = m.tier.value if hasattr(m.tier, "value") else str(m.tier)

        cost_str = f"${m.cost_per_1k_tokens:.4f}/1K"

        st.markdown(
            f"<span style='color:{status_color}'>●</span> "
            f"**{m.name}**  \n"
            f"<span style='color:gray;font-size:0.8em'>{status} | {tier_label} | {cost_str}</span>",
            unsafe_allow_html=True,
        )

    # Refresh button
    if effective_key:
        col1, col2 = st.columns([3, 1])
        with col1:
            updated = st.session_state.get("live_updated")
            if updated:
                st.caption(f"Updated: {updated}")
        with col2:
            st.button(
                "Refresh",
                key="fw_refresh",
                on_click=_on_refresh,
                args=[effective_key],
                use_container_width=True,
            )
    else:
        updated = st.session_state.get("live_updated")
        if updated:
            st.caption(f"Updated: {updated} (no API key)")

    live_error = st.session_state.get("live_error")
    if live_error:
        st.error(live_error)


HISTORY_MAX = 50


def add_to_history(prompt: str, result: dict, elapsed: float) -> None:
    """Append a routing result to session history."""
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append(
        {
            "prompt": prompt,
            "model": result.get("model", "?"),
            "tokens": result.get("tokens", 0),
            "cost": result.get("cost", 0.0),
            "elapsed": round(elapsed, 2),
            "accuracy": result.get("accuracy_score", 0.0),
        }
    )
    if len(st.session_state.history) > HISTORY_MAX:
        st.session_state.history.pop(0)
