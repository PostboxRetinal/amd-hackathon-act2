from src.tasks import classify_task, TaskCategory


def test_classify_math():
    assert classify_task("Calculate 2 + 2") == TaskCategory.MATH
    assert classify_task("Solve x + 5 = 10") == TaskCategory.MATH


def test_classify_code():
    assert classify_task("Write a Python function") == TaskCategory.CODE
    assert classify_task("def hello(): return 'world'") == TaskCategory.CODE


def test_classify_factoid():
    assert classify_task("What is the capital of France?") == TaskCategory.FACTOID


def test_classify_reasoning():
    assert classify_task("Explain why the sky is blue") == TaskCategory.REASONING


def test_classify_creative():
    actual = classify_task("Tell me a science fiction story")
    assert actual in (TaskCategory.CREATIVE, TaskCategory.UNKNOWN)


def test_unknown_fallback():
    assert classify_task("Hello, how are you?") == TaskCategory.UNKNOWN
