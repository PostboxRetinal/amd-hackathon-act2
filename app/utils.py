"""Shared helpers for Wayfinder UI."""

from __future__ import annotations

import time

import streamlit as st

from src.models import get_model
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
