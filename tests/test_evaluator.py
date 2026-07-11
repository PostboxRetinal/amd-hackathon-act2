from src.evaluator import evaluate_response
from src.tasks import TaskCategory


def test_perfect_response():
    score = evaluate_response("What is 2+2?", "4", TaskCategory.MATH)
    assert score > 0.5


def test_refusal_penalty():
    score = evaluate_response("What is 2+2?", "I'm sorry, I cannot answer that.", TaskCategory.MATH)
    assert score < 0.5


def test_empty_response():
    score = evaluate_response("Hello?", "", TaskCategory.UNKNOWN)
    assert score == 0.0


def test_error_response():
    score = evaluate_response("Hello?", "[ERROR]", TaskCategory.UNKNOWN)
    assert score == 0.0


def test_code_contains_code():
    score = evaluate_response("Write a function", "def foo(): pass", TaskCategory.CODE)
    assert score > 0.5


def test_code_missing_code():
    score = evaluate_response("Write a function", "I don't know how to code", TaskCategory.CODE)
    assert score < 0.5


def test_math_no_numbers():
    score = evaluate_response("Calculate 2+2", "The answer is unknown", TaskCategory.MATH)
    assert score < 0.7


def test_factoid_too_long():
    score = evaluate_response("What is the capital of Japan?", "Tokyo is the capital of Japan. " * 20, TaskCategory.FACTOID)
    assert score < 1.0
    assert score > 0.5
