"""Shared helpers for Wayfinder UI."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone

import streamlit as st

from src.models import get_model
from src.router import Router
from src.tasks import TaskCategory


def _on_refresh(fw_key: str) -> None:
    """Refresh callback: fetch live model data from Fireworks API."""
    try:
        data = fetch_fireworks_models(fw_key)
        if data is not None:
            st.session_state.live_models = data
            st.session_state.pop("live_error", None)
        # Also fetch deployment status
        dep_status = fetch_deployment_status(fw_key)
        st.session_state.deployment_status = dep_status
        st.session_state.live_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
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


MODEL_FULL_NAMES = {
    "glm-5p2": "accounts/fireworks/models/glm-5p2",
    "deepseek-v4-pro": "accounts/fireworks/models/deepseek-v4-pro",
    "gemma-4-26b": "accounts/fireworks/models/gemma-4-26b-a4b-it",
    "gemma-4-31b": "accounts/fireworks/models/gemma-4-31b-it",
    "gemma-4-31b-it-nvfp4": "accounts/fireworks/models/gemma-4-31b-it-nvfp4",
    "gemma-4-e4b": "accounts/fireworks/models/gemma-4-e4b",
    "gemma-4-e4b-local": "accounts/fireworks/models/gemma-4-e4b",
}


def _get_model_full_name(model_name: str) -> str:
    """Map a short model name to its full Fireworks API path."""
    return MODEL_FULL_NAMES.get(model_name, model_name)


MODEL_DISPLAY_NAMES = {
    "glm-5p2": "GLM 5.2",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
    "gemma-4-26b": "Gemma 4 26B A4B IT",
    "gemma-4-31b": "Gemma 4 31B IT",
    "gemma-4-31b-it-nvfp4": "Gemma 4 31B IT NVFP4",
    "gemma-4-e4b": "Gemma 4 E4B",
    "gemma-4-e4b-local": "Gemma 4 E4B",
}


def _get_display_name(model_name: str) -> str:
    """Map a short model name to its human-readable display name."""
    return MODEL_DISPLAY_NAMES.get(model_name, model_name)


MODEL_URLS = {
    "gemma-4-26b": "https://fireworks.ai/models/fireworks/gemma-4-26b-a4b-it",
    "gemma-4-31b": "https://fireworks.ai/models/fireworks/gemma-4-31b-it",
    "gemma-4-31b-it-nvfp4": "https://fireworks.ai/models/fireworks/gemma-4-31b-it-nvfp4",
    "gemma-4-e4b": "https://fireworks.ai/models/fireworks/gemma-4-e4b",
    "deepseek-v4-pro": "https://fireworks.ai/models/fireworks/deepseek-v4-pro",
    "glm-5p2": "https://fireworks.ai/models/fireworks/glm-5p2",
}


def _get_model_url(model_name: str) -> str:
    return MODEL_URLS.get(model_name, "#")


def display_as_cli(result: dict, elapsed: float) -> None:
    """Render result summary as a polished output card."""
    model_raw = result.get("model", "?")
    model = _get_display_name(model_raw)
    full_name = _get_model_full_name(model_raw)
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
            f"<span style='color:{status_color}'>●</span> **{model}**  \n`{full_name}`",
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

        st.markdown(f"**Accuracy:** {acc_str}  ·  **Fallback:** {'yes' if fb else 'no'}")
        st.caption(f"Completed in {elapsed:.1f}s")


def display_metrics(result: dict, elapsed: float) -> None:
    """Show key metrics in columns below the CLI block."""
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        st.metric("Model", _get_display_name(result["model"]))
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
                st.markdown(f"**Name:** {_get_display_name(result['model'])}")
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
        f"**Done!** `{_get_display_name(model)}` | {elapsed:.1f}s | {tokens:,} tokens | ${cost:.6f}"
    )
    st.divider()


def validate_api_key(api_key: str) -> bool:
    """Check if the Fireworks API key is valid by calling /v1/models."""
    import urllib.request

    req = urllib.request.Request(
        "https://api.fireworks.ai/inference/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def fetch_fireworks_models(api_key: str) -> dict | None:
    """Fetch pricing for Wayfinder's models from Fireworks AI API.

    Returns a dict with 'pricing' (keyed by model name) and
    'available_ids' (list of expected model IDs found in the API response),
    filtered to only the models we use in routing.
    """

    wayfinder_models = {
        "deepseek-v4-pro": "accounts/fireworks/models/deepseek-v4-pro",
        "glm-5p2": "accounts/fireworks/models/glm-5p2",
        "gemma-4-26b": "accounts/fireworks/models/gemma-4-26b-a4b-it",
        "gemma-4-31b": "accounts/fireworks/models/gemma-4-31b-it",
        "gemma-4-31b-it-nvfp4": "accounts/fireworks/models/gemma-4-31b-it-nvfp4",
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


def fetch_deployment_status(api_key: str) -> dict:
    """Fetch deployment status from Fireworks control plane API.

    Returns dict keyed by deployment model ID:
    {"txbj700w": {"state": "READY", "replicas": 2, "model": "gemma-4-26b"}}
    """
    # Extract account ID from our deployment model ID
    # e.g., "accounts/postboxretinal/deployments/txbj700w"
    deployment_ref = "accounts/postboxretinal/deployments/txbj700w"
    parts = deployment_ref.split("/")
    account_id = parts[1]  # "postboxretinal"

    req = urllib.request.Request(
        f"https://api.fireworks.ai/v1/accounts/{account_id}/deployments",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return {}

    result = {}
    deployments = data if isinstance(data, list) else data.get("deployments", [])
    for dep in deployments:
        dep_id = dep.get("id", "")
        state = dep.get("state", "UNKNOWN")
        replica_stats = dep.get("replica_stats", {})
        ready = replica_stats.get("ready", 0)
        model_name = dep.get("base_model", "")
        # Extract short ID from full path
        short_id = dep_id.split("/")[-1] if "/" in dep_id else dep_id
        result[short_id] = {
            "state": state,
            "replicas": ready,
            "model": model_name,
        }
    return result


# Category labels for models
MODEL_CATEGORIES = {
    "deepseek": "code/math",
    "glm-5p2": "reasoning",
    "gemma-4-31b": "general",
    "gemma-4-26b": "dedicated",
    "gemma-4-e4b": "local (ROCm)",
}


def _get_model_status(m, live_pricing, available_ids):
    """Return (status_label, color, live_id) for a model."""
    if "gemma" in m.name.lower():
        status, status_color = "SETUP", "orange"
    elif m.provider == "local":
        status, status_color = "DOWN", "red"
    elif live_pricing:
        status = "UP" if m.model_id in available_ids else "SETUP"
        status_color = "green" if status == "UP" else "orange"
    else:
        status = "UP" if "deployments" not in m.model_id else "SETUP"
        status_color = "green" if status == "UP" else "orange"
    return status, status_color, None


def _get_category(name: str) -> str:
    """Determine the category label for a model name."""
    for key, label in MODEL_CATEGORIES.items():
        if key in name.lower():
            return label
    return "general"


def display_model_pool(router: Router, api_key: str | None = None) -> None:
    """Show model pool as compact status cards with colors."""
    if "live_models" not in st.session_state:
        st.session_state.live_models = {}
    if "live_updated" not in st.session_state:
        st.session_state.live_updated = None
    if "deployment_status" not in st.session_state:
        st.session_state.deployment_status = {}

    all_models = router._all()
    effective_key = api_key or os.environ.get("FIREWORKS_API_KEY")
    live = st.session_state.get("live_models", {})
    live_pricing = live.get("pricing", {})
    available_ids = live.get("available_ids", set())

    # Separate serverless from dedicated deployments
    serverless_models = []
    deployment_models = []

    for m in all_models:
        if m.provider == "local":
            deployment_models.append(m)
        elif "deployments" in m.model_id:
            deployment_models.append(m)
        elif "gemma-4-31b" in m.name.lower():
            deployment_models.append(m)
        else:
            serverless_models.append(m)

    # Render serverless section
    if serverless_models:
        # LIVE badge if we have fresh pricing data
        has_live = any(live_pricing.get(m.name, {}).get("prompt_cost") for m in serverless_models)
        live_badge = (
            " <span style='color:#00D4AA;font-size:0.7em;border:1px solid #00D4AA;"
            "border-radius:4px;padding:0 6px'>LIVE</span>"
            if has_live
            else ""
        )
        st.markdown(f"**Serverless**{live_badge}", unsafe_allow_html=True)
        for m in serverless_models:
            status, status_color, _ = _get_model_status(m, live_pricing, available_ids)
            category = _get_category(m.name)

            # Prefer live pricing/context from API, fall back to static config
            live_info = live_pricing.get(m.name, {})
            live_prompt_cost = live_info.get("prompt_cost")
            if live_prompt_cost and float(live_prompt_cost) > 0:
                live_cost = float(live_prompt_cost) * 1000
                cost_str = f"${live_cost:.4f}/1K"
            else:
                cost_str = f"${m.cost_per_1k_tokens:.4f}/1K"

            live_ctx = live_info.get("context_length")
            if live_ctx and int(live_ctx) > 0:
                ctx = f"{int(live_ctx):,}"
            else:
                ctx = f"{m.context_limit:,}" if m.context_limit else "N/A"

            hover_parts = [f"Model: {_get_display_name(m.name)}", f"Category: {category}"]
            hover_text = " | ".join(hover_parts)

            # Get full Fireworks path
            full_path = _get_model_full_name(m.name)

            # Color by model family
            if "deepseek" in m.name.lower():
                dot_color = "#7C3AED"  # purple
            elif "glm" in m.name.lower():
                dot_color = "#FFFFFF"  # white
            elif "gemma-4-26b" in m.name.lower():
                dot_color = "#4A90D9"  # medium blue
            elif "nvfp4" in m.name.lower():
                dot_color = "#00D4AA"  # teal/green for Nvidia
            elif "gemma-4-31b" in m.name.lower():
                dot_color = "#2E6CB5"  # dark blue
            elif "gemma-4-e4b" in m.name.lower():
                dot_color = "#6BB3E0"  # light blue
            else:
                dot_color = "#888888"  # gray fallback

            # Build 3-line display
            st.markdown(
                f"<span title='{hover_text}' style='cursor:help'>"
                f"<span style='color:{dot_color}'>●</span> "
                f"**{_get_display_name(m.name)}** [\u2197]({_get_model_url(m.name)})  \n"
                f"<span style='color:gray;font-size:0.75em'>{full_path}</span>  \n"
                f"<span style='color:gray;font-size:0.8em'>{category} | {cost_str} | {ctx} ctx</span>"
                f"</span>",
                unsafe_allow_html=True,
            )
    # Render deployments section
    if deployment_models:
        st.markdown("**Deployments**")
        st.markdown(
            "[Create new deployment \u2192](https://app.fireworks.ai/dashboard/deployments/create)"
        )
        for m in deployment_models:
            status, status_color, _ = _get_model_status(m, live_pricing, available_ids)
            # Prefer live pricing/context from API, fall back to static config
            live_info = live_pricing.get(m.name, {})
            live_prompt_cost = live_info.get("prompt_cost")
            if live_prompt_cost and float(live_prompt_cost) > 0:
                live_cost = float(live_prompt_cost) * 1000
                cost_str = f"${live_cost:.4f}/1K"
            else:
                cost_str = f"${m.cost_per_1k_tokens:.4f}/1K"

            live_ctx = live_info.get("context_length")
            if live_ctx and int(live_ctx) > 0:
                ctx = f"{int(live_ctx):,}"
            else:
                ctx = f"{m.context_limit:,}" if m.context_limit else "N/A"

            hover_parts = [f"Model: {_get_display_name(m.name)}", "Category: dedicated"]
            hover_text = " | ".join(hover_parts)

            # Get full Fireworks path
            full_path = _get_model_full_name(m.name)

            # Color by model family
            if "deepseek" in m.name.lower():
                dot_color = "#7C3AED"  # purple
            elif "glm" in m.name.lower():
                dot_color = "#FFFFFF"  # white
            elif "gemma-4-26b" in m.name.lower():
                dot_color = "#4A90D9"  # medium blue
            elif "nvfp4" in m.name.lower():
                dot_color = "#00D4AA"  # teal/green for Nvidia
            elif "gemma-4-31b" in m.name.lower():
                dot_color = "#2E6CB5"  # dark blue
            elif "gemma-4-e4b" in m.name.lower():
                dot_color = "#6BB3E0"  # light blue
            else:
                dot_color = "#888888"  # gray fallback

            category = "dedicated"

            # Build 3-line display
            st.markdown(
                f"<span title='{hover_text}' style='cursor:help'>"
                f"<span style='color:{dot_color}'>●</span> "
                f"**{_get_display_name(m.name)}** [\u2197]({_get_model_url(m.name)})  \n"
                f"<span style='color:gray;font-size:0.75em'>{full_path}</span>  \n"
                f"<span style='color:gray;font-size:0.8em'>{cost_str} | {ctx} ctx</span>"
                f"</span>",
                unsafe_allow_html=True,
            )

    # Refresh button
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
            st.caption(f"Last refresh: {updated}")
    else:
        updated = st.session_state.get("live_updated")
        if updated:
            st.caption(f"Last refresh: {updated} (no API key)")

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
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "task_category": result.get("task_category"),
        }
    )
    if len(st.session_state.history) > HISTORY_MAX:
        st.session_state.history.pop(0)
