"""Run Streamlit in dev mode with debug logging + exception traceback."""

import os
import shutil
import subprocess
import sys


def _clean_cache():
    """Remove all __pycache__ and .pyc files to prevent stale widget issues."""
    root = os.path.join(os.path.dirname(__file__), "..")
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .venv and .git
        rel = os.path.relpath(dirpath, root)
        if rel.startswith(".venv") or rel.startswith(".git"):
            continue
        # Remove __pycache__ directories
        if "__pycache__" in dirnames:
            cache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(cache_path, ignore_errors=True)
            dirnames.remove("__pycache__")
        # Remove .pyc files (in case any are loose)
        for f in filenames:
            if f.endswith(".pyc"):
                try:
                    os.remove(os.path.join(dirpath, f))
                except OSError:
                    pass


def main():
    """Entry point: run streamlit with debug logging."""
    print("[dev] Cleaning Python cache...", flush=True)
    _clean_cache()
    print("[dev] Starting Streamlit...", flush=True)
    env = {**os.environ, "STREAMLIT_LOGGER_LEVEL": "debug"}
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/main.py",
        "--server.port=8501",
        "--logger.level=debug",
    ]
    sys.exit(subprocess.call(cmd, env=env))


if __name__ == "__main__":
    main()
