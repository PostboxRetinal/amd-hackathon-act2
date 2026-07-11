"""Tests for the response evaluator."""

from src.evaluator import evaluate_response
from src.tasks import TaskCategory


def test_perfect_response():
    """A good, substantive response should score high."""
    score = evaluate_response(
        "Explain quantum computing",
        "Quantum computing uses quantum bits (qubits) which can exist in superposition, "
        "allowing parallel computation across many states simultaneously.",
        TaskCategory.REASONING,
    )
    assert score >= 0.7


def test_empty_response():
    """An empty response should score 0.0."""
    assert evaluate_response("What is 2+2?", "", TaskCategory.MATH) == 0.0


def test_error_response():
    """An [ERROR] response should score 0.0."""
    assert evaluate_response("What is 2+2?", "[ERROR]", TaskCategory.MATH) == 0.0


def test_refusal_penalty():
    """A refusal response should be penalized."""
    score = evaluate_response(
        "Tell me about history",
        "I'm sorry, but I cannot help with that request.",
        TaskCategory.FACTOID,
    )
    assert score < 1.0


def test_code_contains_code():
    """A code response with code blocks should not be penalized for missing code."""
    score = evaluate_response(
        "Write a function",
        "Here is your function:\n```python\ndef hello():\n    print('hello')\n```",
        TaskCategory.CODE,
    )
    assert score >= 0.7


def test_code_missing_code():
    """A code response without any code markers should be penalized."""
    score = evaluate_response(
        "Write a function",
        "Sure, I can help with that.",
        TaskCategory.CODE,
    )
    assert score < 0.7


def test_math_no_numbers():
    """A math response without any digits should be penalized."""
    score = evaluate_response(
        "What is two plus two?",
        "The answer is four.",
        TaskCategory.MATH,
    )
    assert score < 0.7


def test_factoid_too_long():
    """A factoid response that is too long should be penalized."""
    long_response = "The capital of France is Paris. " * 20
    score = evaluate_response(
        "What is the capital of France?",
        long_response,
        TaskCategory.FACTOID,
    )
    assert score < 1.0
