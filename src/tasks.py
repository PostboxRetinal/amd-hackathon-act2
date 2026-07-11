from enum import Enum


class TaskCategory(Enum):
    MATH = "math"
    CODE = "code"
    REASONING = "reasoning"
    FACTOID = "factoid"
    CREATIVE = "creative"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    UNKNOWN = "unknown"


def classify_task(prompt: str) -> TaskCategory:
    """
    Classify a task based on prompt heuristics.
    Returns the most likely TaskCategory.
    """
    p = prompt.lower()

    # Math and arithmetic
    if any(
        kw in p
        for kw in [
            "calculate",
            "compute",
            "solve",
            "math",
            "equation",
            "formula",
            "sum",
            "add",
            "subtract",
            "multiply",
            "divide",
        ]
    ):
        return TaskCategory.MATH

    # Code generation
    if any(
        kw in p
        for kw in [
            "function",
            "def ",
            "class ",
            "import ",
            "code",
            "implement",
            "write a program",
            "script",
            "algorithm",
            "function that",
            "html",
            "javascript",
            "python",
            "c++",
            "rust",
            "typescript",
        ]
    ):
        return TaskCategory.CODE

    # Logic and reasoning
    if any(
        kw in p
        for kw in [
            "explain why",
            "reason",
            "logic",
            "deduce",
            "infer",
            "conclusion",
            "hypothesis",
            "if then",
            "therefore",
            "because",
        ]
    ):
        return TaskCategory.REASONING

    # Simple factual questions
    if len(p) < 120 and any(
        kw in p
        for kw in [
            "who",
            "what is",
            "when",
            "where",
            "capital of",
            "definition",
            "meaning of",
            "define",
        ]
    ):
        return TaskCategory.FACTOID

    # Classification
    if any(
        kw in p
        for kw in [
            "classify",
            "categorize",
            "tag",
            "label",
        ]
    ):
        return TaskCategory.CLASSIFICATION

    # Summarization
    if any(
        kw in p
        for kw in [
            "summarize",
            "summary",
            "tl;dr",
            "synopsis",
        ]
    ):
        return TaskCategory.SUMMARIZATION

    # Extraction
    if any(
        kw in p
        for kw in [
            "extract",
            "find all",
            "list all",
            "pull out",
        ]
    ):
        return TaskCategory.EXTRACTION

    # Creative
    if any(
        kw in p
        for kw in [
            "write a story",
            "poem",
            "creative",
            "tell me a",
            "write a tale",
            "narrative",
        ]
    ):
        return TaskCategory.CREATIVE

    return TaskCategory.UNKNOWN
