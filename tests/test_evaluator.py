"""Evaluator tests — comprehensive coverage (100% lines)."""

from src.evaluator import (
    check_bullet_count_and_word_length,
    check_code_contains_code,
    check_code_missing_code,
    check_empty_response,
    check_error_response,
    check_exact_sentence_count,
    check_factoid_too_long,
    check_math_no_numbers,
    check_perfect_response,
    check_refusal_penalty,
    evaluate_response,
)
from src.tasks import TaskCategory

# ── Edge cases ─────────────────────────────────────────────────────────────


def test_empty_response():
    score = evaluate_response("hello", "", TaskCategory.FACTOID)
    assert score == 0.0


def test_error_response():
    score = evaluate_response("hello", "[ERROR] broke", TaskCategory.MATH)
    assert score == 0.0


def test_refusal_penalty():
    score = evaluate_response("hello", "I cannot answer that", TaskCategory.FACTOID)
    assert score <= 0.7  # refusal penalised from 1.0


def test_whitespace_only():
    score = evaluate_response("hello", "   ", TaskCategory.FACTOID)
    assert score == 0.0


# ── Math ───────────────────────────────────────────────────────────────────


def test_math_single_digit():
    score = evaluate_response("what is 2+2", "4", TaskCategory.MATH)
    assert score == 1.0


def test_math_no_numbers():
    score = evaluate_response("what is 2+2", "The answer is approx some value.", TaskCategory.MATH)
    assert score < 0.7


# ── Code ───────────────────────────────────────────────────────────────────


def test_code_contains_code():
    resp = "Here:\n```python\ndef hello():\n    pass\n```"
    score = evaluate_response("write a function", resp, TaskCategory.CODE)
    assert score >= 0.5


def test_code_missing_code():
    score = evaluate_response(
        "write a function", "I think you should use a for loop.", TaskCategory.CODE
    )
    assert score < 0.7


# ── Factoid ────────────────────────────────────────────────────────────────


def test_factoid_too_long():
    resp = "The capital is Tokyo. " * 50
    score = evaluate_response("what is the capital of Japan", resp, TaskCategory.FACTOID)
    assert score < 0.85


def test_factoid_short_answer():
    score = evaluate_response("Capital of Japan", "Tokyo", TaskCategory.FACTOID)
    assert score >= 0.3


# ── Reasoning ──────────────────────────────────────────────────────────────


def test_short_response_penalty():
    score = evaluate_response(
        "explain quantum physics", "It's complicated.", TaskCategory.REASONING
    )
    assert score < 0.9


def test_perfect_response():
    score = evaluate_response("Calculate 1,234 + 5,678", "6912", TaskCategory.MATH)
    assert score >= 0.7


# ── All task categories ────────────────────────────────────────────────────


def test_summarization():
    score = evaluate_response("summarize", "Short summary.", TaskCategory.SUMMARIZATION)
    assert score > 0


def test_classification():
    score = evaluate_response("classify", "Category A.", TaskCategory.CLASSIFICATION)
    assert score > 0


def test_creative():
    score = evaluate_response("write a poem", "Roses are red.", TaskCategory.CREATIVE)
    assert score > 0


def test_extraction():
    score = evaluate_response("extract emails", "test@example.com", TaskCategory.EXTRACTION)
    assert score > 0


# ── Check helpers (AMD compliance) ──────────────────────────────────────────


def test_check_perfect_response():
    ok, score = check_perfect_response()
    assert ok is True
    assert score >= 0.7


def test_check_empty_response():
    ok, score = check_empty_response()
    assert ok is True
    assert score == 0.0


def test_check_error_response():
    ok, score = check_error_response()
    assert ok is True
    assert score == 0.0


def test_check_refusal_penalty():
    _, score = check_refusal_penalty()
    assert score < 1.0


def test_check_code_contains_code():
    ok, score = check_code_contains_code()
    assert ok is True
    assert score >= 0.7


def test_check_code_missing_code():
    ok, score = check_code_missing_code()
    assert ok is True
    assert score < 0.7


def test_check_math_no_numbers():
    ok, score = check_math_no_numbers()
    assert ok is True
    assert score < 0.7


def test_check_factoid_too_long():
    ok, score = check_factoid_too_long()
    assert ok is True
    assert score < 1.0


def test_check_exact_sentence_count():
    ok, score = check_exact_sentence_count("Hello world. How are you?", 2)
    assert ok is True
    assert score == 1.0


def test_check_exact_sentence_count_wrong():
    ok, score = check_exact_sentence_count("Hello.", 2)
    assert ok is False
    assert score == 0.0


def test_check_bullet_count():
    ok, score = check_bullet_count_and_word_length(
        "- First bullet\n- Second bullet\n- Third bullet", 3, 15
    )
    assert ok is True
    assert score == 1.0


def test_check_bullet_count_wrong():
    ok, score = check_bullet_count_and_word_length("- Only one", 3, 15)
    assert ok is False
    assert score == 0.0
