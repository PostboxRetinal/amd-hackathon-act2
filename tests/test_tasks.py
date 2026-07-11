"""Tests for the task classifier."""

from src.tasks import TaskCategory, classify_task


def test_classify_math():
    """Math-related prompts should classify as MATH."""
    assert classify_task("Calculate 15 * 23") == TaskCategory.MATH


def test_classify_code():
    """Code-related prompts should classify as CODE."""
    assert classify_task("Write a Python function that sorts a list") == TaskCategory.CODE


def test_classify_reasoning():
    """Reasoning prompts should classify as REASONING."""
    assert classify_task("Explain why the sky is blue, step by step") == TaskCategory.REASONING


def test_classify_factoid():
    """Short factual prompts should classify as FACTOID."""
    assert classify_task("What is the capital of France?") == TaskCategory.FACTOID


def test_classify_creative():
    """Creative prompts should classify as CREATIVE."""
    assert classify_task("Write a story about a dragon") == TaskCategory.CREATIVE


def test_unknown_fallback():
    """Unrecognizable prompts should fall back to UNKNOWN."""
    assert classify_task("xyzzy frobnicate") == TaskCategory.UNKNOWN
