"""Shared helpers for Wayfinder UI."""

from __future__ import annotations

import json
import os
import time
import urllib.request

import pandas as pd
import streamlit as st
from streamlit.column_config import TextColumn

from src.models import get_model
from src.router import Router
from src.tasks import TaskCategory


# Emoji badges per task category (kept in comments/data, not inline code).
_TASK_META: dict[TaskCategory, tuple[str, str]] = {
    TaskCategory.MATH: ("math", "Math"),
    TaskCategory.CODE: ("code", "Code"),
    TaskCategory.REASONING: ("brain", "Reasoning"),
    TaskCategory.FACTOID: ("fact", "Factoid"),
    TaskCategory.CREATIVE: ("creative", "Creative"),
    TaskCategory.CLASSIFICATION: ("tag", "Classification"),
    TaskCategory.SUMMARIZATION: ("doc", "Summarization"),
    TaskCategory.EXTRACTION: ("extract", "Extraction"),
    TaskCategory.UNKNOWN: ("question", "Unknown"),
}


def display_as_cli(result: dict, elapsed: float) -> None:
    """Render result identical to CLI output from src/__main__.py."""
    fb = "Yes" if result["fallback_used"] else "No"
    response_preview = result["response"][:200]
    if len(result["response"]) > 200:
        response_preview += "..."
    cli = (
        f"Model:         {result['model']}\n"
        f"Accuracy:      {result['accuracy_score']:.2f}\n"
        f"Tokens:        {result['tokens']}\n"
        f"Cost:          ${result['cost']:.6f}\n"
        f"Fallback used: {fb}\n"
        f"Response:      {response_preview}\n"
    )
    st.code(cli, language="text")


def display_response(text: str) -> None:
    """Show response in a code block."""
    st.markdown("**Response:**")
    st.code(text, language="text", wrap_lines=True)


def task_badge(task: TaskCategory) -> str:
    """Return an emoji + label string for the task category."""
    emoji, label = _TASK_META.get(task, _TASK_META[TaskCategory.UNKNOWN])
    return f"{emoji} {label}"


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


def display_model_details(result: dict) -> None:
    """Expander with full model details from the catalog."""
    with st.expander("Model Details", expanded=False):
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


def fetch_fireworks_models(api_key: str) -> dict[str, dict] | None:
    """Fetch pricing for Wayfinder's models from Fireworks AI API.

    Returns a dict keyed by model name with pricing and context info,
    filtered to only the models we use in routing.
    """

    WAYFINDER_MODELS = {
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

    result = {}
    for m in data:
        mid = m.get("id", "")
        for name, expected_id in WAYFINDER_MODELS.items():
            if mid == expected_id or name in mid:
                cost = m.get("pricing", {})
                result[name] = {
                    "id": mid,
                    "display_name": m.get("display_name", name),
                    "prompt_cost": cost.get("prompt", 0),
                    "completion_cost": cost.get("completion", 0),
                    "context_length": m.get("context_length", 0),
                }
                break
    return result


def display_model_pool(router: Router, api_key: str | None = None) -> None:
    """Show the pool of available models with live pricing and status."""
    from datetime import datetime

    if "live_models" not in st.session_state:
        st.session_state.live_models = {}
    if "live_updated" not in st.session_state:
        st.session_state.live_updated = None

    all_models = router._all()
    effective_key = api_key or os.environ.get("FIREWORKS_API_KEY")

    def _on_refresh(fw_key: str) -> None:
        try:
            data = fetch_fireworks_models(fw_key)
            if data is not None:
                st.session_state.live_models = data
                st.session_state.live_updated = datetime.now().strftime("%H:%M")
                st.session_state.pop("live_error", None)
            else:
                st.session_state.live_error = "API call failed or returned empty"
        except Exception:
            st.session_state.live_error = "Refresh failed - check API key or network"

    st.markdown("**Model Pool**")

    if effective_key:
        st.button(
            "Refresh",
            key="fw_refresh",
            on_click=_on_refresh,
            args=[effective_key],
            use_container_width=True,
        )
        updated = st.session_state.get("live_updated")
        if updated:
            st.caption(f"Updated: {updated}")
    else:
        updated = st.session_state.get("live_updated")
        if updated:
            st.caption(f"Updated: {updated}")

    live_error = st.session_state.get("live_error")
    if live_error:
        st.error(live_error)

    all_models = router._all()
    live = st.session_state.get("live_models", {})

    rows = []
    for m in all_models:
        live_info = live.get(m.name, {})
        prompt_cost = live_info.get("prompt_cost")
        ctx = live_info.get("context_length")

        # Status determination
        if "gemma" in m.name.lower():
            status = "SETUP"
        elif m.provider == "local":
            status = "DOWN"
        elif "deployments" in m.model_id:
            status = "SETUP"
        else:
            status = "UP"

        # Cost
        if prompt_cost is not None:
            cost_str = f"${prompt_cost:.4f}"
        else:
            cost_str = f"${m.cost_per_1k_tokens:.4f}"

        # Context length
        ctx_str = f"{ctx:,}" if ctx else f"{m.context_limit:,}"

        # Tier
        tier_label = m.tier.value if hasattr(m.tier, "value") else str(m.tier)

        rows.append({
            "Status": status,
            "Model": m.name,
            "Tier": tier_label,
            "Provider": m.provider,
            "Cost": cost_str,
            "Context": ctx_str,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            column_config={
                "Status": TextColumn("Status", width="small"),
                "Model": TextColumn("Model"),
                "Tier": TextColumn("Tier", width="small"),
                "Provider": TextColumn("Provider", width="small"),
                "Cost": TextColumn("Cost", width="small"),
                "Context": TextColumn("Context", width="small"),
            },
            hide_index=True,
            width="stretch",
        )


def add_to_history(prompt: str, result: dict, elapsed: float) -> None:
    """Append a query+result to session-state history (max 5)."""
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append(
        {
            "prompt": prompt,
            "result": result,
            "elapsed": elapsed,
            "timestamp": time.strftime("%H:%M:%S"),
        }
    )
    if len(st.session_state.history) > 5:
        st.session_state.history = st.session_state.history[-5:]
