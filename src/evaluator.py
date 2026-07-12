from src.tasks import TaskCategory


def evaluate_response(prompt: str, response: str, task: TaskCategory) -> float:
    """
    Score a response from 0.0 to 1.0.

    1.0 = perfect, 0.0 = completely useless.
    Uses heuristics — no external model calls.
    """
    if not response or len(response.strip()) < 1:
        return 0.0

    # Detect API-level errors immediately
    if response.strip().startswith("[ERROR"):
        return 0.0

    # Single-digit answers are valid for math
    if task == TaskCategory.MATH and response.strip().isdigit():
        return 1.0

    score = 1.0

    # Penalize refusal / non-answers
    refusal = [
        "sorry",
        "i'm sorry",
        "i cannot",
        "i don't know",
        "as an ai",
        "not able to",
        "unable to",
        "do not have",
    ]
    for phrase in refusal:
        if phrase in response.lower():
            score -= 0.3
            break

    # Factoid answers should be concise
    if task == TaskCategory.FACTOID and len(response) > 200:
        score -= 0.2

    # Code should contain code
    if task == TaskCategory.CODE:
        if "```" not in response and "def " not in response and "function" not in response:
            score -= 0.4

    # Math should contain numbers or show work
    if task == TaskCategory.MATH:
        if not any(c.isdigit() for c in response):
            score -= 0.4

    # Short responses are OK for math and factoid
    if task not in (TaskCategory.MATH, TaskCategory.FACTOID) and len(response.split()) < 3:
        score -= 0.5

    return max(0.0, min(1.0, score))


def check_perfect_response(
    response: str = "Quantum computing uses quantum bits (qubits) which can exist in superposition, allowing parallel computation across many states simultaneously.",
) -> tuple[bool, float]:
    """A good, substantive response should score high."""
    score = evaluate_response("Explain quantum computing", response, TaskCategory.REASONING)
    return score >= 0.7, score


def check_empty_response(response: str = "") -> tuple[bool, float]:
    """An empty response should score 0.0."""
    score = evaluate_response("What is 2+2?", response, TaskCategory.MATH)
    return score == 0.0, score


def check_error_response(response: str = "[ERROR]") -> tuple[bool, float]:
    """An [ERROR] response should score 0.0."""
    score = evaluate_response("What is 2+2?", response, TaskCategory.MATH)
    return score == 0.0, score


def check_refusal_penalty(
    response: str = "I'm sorry, but I cannot help with that request.",
) -> tuple[bool, float]:
    """A refusal response should be penalized."""
    score = evaluate_response("Tell me about history", response, TaskCategory.FACTOID)
    return score < 1.0, score


def check_code_contains_code(
    response: str = "Here is your function:\n```python\ndef hello():\n    print('hello')\n```",
) -> tuple[bool, float]:
    """A code response with code blocks should not be penalized for missing code."""
    score = evaluate_response("Write a function", response, TaskCategory.CODE)
    return score >= 0.7, score


def check_code_missing_code(response: str = "Sure, I can help with that.") -> tuple[bool, float]:
    """A code response without any code markers should be penalized."""
    score = evaluate_response("Write a function", response, TaskCategory.CODE)
    return score < 0.7, score


def check_math_no_numbers(response: str = "The answer is four.") -> tuple[bool, float]:
    """A math response without any digits should be penalized."""
    score = evaluate_response("What is two plus two?", response, TaskCategory.MATH)
    return score < 0.7, score


def check_factoid_too_long(
    response: str = "The capital of France is Paris. " * 20,
) -> tuple[bool, float]:
    """A factoid response that is too long should be penalized."""
    score = evaluate_response("What is the capital of France?", response, TaskCategory.FACTOID)
    return score < 1.0, score


def check_exact_sentence_count(response: str, expected: int = 2) -> tuple[bool, float]:
    """Check the response has exactly `expected` sentences."""
    sentences = [
        s.strip() for s in response.replace("? ", ".").replace("! ", ".").split(".") if s.strip()
    ]
    if len(sentences) == expected:
        return True, 1.0
    return False, 0.0


def check_bullet_count_and_word_length(
    response: str, expected_bullets: int = 3, max_words: int = 15
) -> tuple[bool, float]:
    """Check the response has exactly `expected_bullets` bullet points, each under `max_words` words."""
    import re

    bullets = re.findall(r"^[\s]*[-*+][\s]+(.+)$", response, re.MULTILINE)
    if len(bullets) != expected_bullets:
        return False, 0.0
    for b in bullets:
        if len(b.split()) > max_words:
            return False, 0.0
    return True, 1.0


_ALL_TESTS = [
    check_perfect_response,
    check_empty_response,
    check_error_response,
    check_refusal_penalty,
    check_code_contains_code,
    check_code_missing_code,
    check_math_no_numbers,
    check_factoid_too_long,
    check_exact_sentence_count,
    check_bullet_count_and_word_length,
]
