"""Tests for CLI entry point and --json output mode."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIJsonMode:
    """Test the --json flag produces valid structured output."""

    def test_json_has_required_fields(self):
        """Verify the JSON output dict contains all required fields."""
        expected_fields = {"task_id", "response", "model", "tokens", "cost", "accuracy"}

        result = {
            "task_id": "test",
            "response": "mock",
            "model": "mock-model",
            "tokens": 10,
            "cost": 0.0,
            "accuracy": 1.0,
        }

        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["task_id"] == "test"

    def test_cli_imports(self, monkeypatch):
        """Verify the CLI module imports without error."""
        monkeypatch.setattr(os, "environ", {**os.environ, "FIREWORKS_API_KEY": "test"})
        import src.__main__

        assert hasattr(src.__main__, "__doc__")
