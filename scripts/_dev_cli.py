"""Run Streamlit in dev mode with debug logging + exception traceback."""

import os
import subprocess
import sys


def main():
    """Entry point: run streamlit with debug logging."""
    env = {**os.environ, "STREAMLIT_LOGGER_LEVEL": "debug"}
    cmd = [sys.executable, "-m", "streamlit", "run", "app/main.py", "--logger.level=debug"]
    sys.exit(subprocess.call(cmd, env=env))


if __name__ == "__main__":
    main()
