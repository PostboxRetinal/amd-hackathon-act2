"""Shared helpers for Wayfinder UI."""

from __future__ import annotations

import json
import os
import time
import urllib.request

import streamlit as st

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


def display_fireworks_pool(api_key: str) -> None:
    """Display a 'Refresh' button that fetches live pricing for Wayfinder models."""
    refresh_col, status_col = st.columns([1, 2])
    with refresh_col:
        refresh_clicked = st.button("\U0001f504 Refresh", key="fw_refresh", use_container_width=True)
    with status_col:
        if refresh_clicked:
            st.caption("Fetching...")

    if refresh_clicked:
        live = fetch_fireworks_models(api_key)
        if live:
            st.success(f"Updated {len(live)} models")
            for name, info in live.items():
                st.markdown(
                    f"<div style='font-size:12px; padding:2px 0;'>"
                    f"<strong>{name}</strong> "
                    f"<span style='color:#888;'>| "
                    f"${info['prompt_cost']:.4f}/${info['completion_cost']:.4f} per token "
                    f"| ctx: {info['context_length']:,}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.error("Failed to fetch from Fireworks API")


def display_model_pool(router: Router, api_key: str | None = None) -> None:
    """Show the pool of available models with their status."""
    all_models = router._all()

    data = []
    for m in all_models:
        # Determine status
        if m.provider == "local":
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                host, port_str = m.model_id.split("://")[1].split("/")[0].split(":")
                port = int(port_str)
                status = s.connect_ex((host, port)) == 0
                s.close()
                status_label = "Ready" if status else "Down"
            except Exception:
                status_label = "Down"
        elif m.provider == "fireworks" and "deployments" in m.model_id:
            status_label = "Paused"
        else:
            status_label = "Ready"

        data.append({
            "Model": m.name,
            "Tier": m.tier.value if hasattr(m.tier, "value") else str(m.tier),
            "Provider": m.provider,
            "Cost/1K": f"${m.cost_per_1k_tokens:.4f}" if m.cost_per_1k_tokens > 0 else "$0.00",
            "Status": status_label,
        })

    st.markdown("**Model Pool**")

    for entry in data:
        status = entry["Status"]
        if status == "Ready":
            icon = "[OK]"
        elif status == "Paused":
            icon = "[PAUSED]"
        else:
            icon = "[RED]"

        st.markdown(
            f"<div style='font-size:13px; padding:2px 0;'>"
            f"{icon} <strong>{entry['Model']}</strong> "
            f"<span style='color:#888;'>| {entry['Tier']} | {entry['Cost/1K']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Refresh from Fireworks button
    effective_key = api_key or os.environ.get("FIREWORKS_API_KEY")
    if effective_key:
        st.divider()
        display_fireworks_pool(effective_key)


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
