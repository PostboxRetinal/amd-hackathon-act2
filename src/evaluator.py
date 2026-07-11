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
    if response.strip() == "[ERROR]":
        return 0.0

    # Single-digit answers are valid for math
    if task == TaskCategory.MATH and response.strip().isdigit():
        return 1.0

    score = 1.0

    # Penalize refusal / non-answers
    refusal = [
        "cannot", "sorry", "i'm sorry", "i cannot",
        "i don't know", "as an ai", "not able to",
        "unable to", "do not have", "error",
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
