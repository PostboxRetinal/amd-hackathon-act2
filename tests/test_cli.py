"""CLI test — minimal smoke test."""

import sys

PROJECT_ROOT = None


def test_cli_imports():
    """The HELP_TEXT constant exists."""
    old_argv = sys.argv
    sys.argv = ["wayfinder", "--version"]
    try:
        from src.__main__ import HELP_TEXT

        assert "Usage" in HELP_TEXT
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
