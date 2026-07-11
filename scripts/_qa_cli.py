"""uv run qa entry point. Delegates to scripts/qa.sh."""

import subprocess
import sys


def main() -> None:
    sys.exit(subprocess.call(["bash", "scripts/qa.sh"]))


if __name__ == "__main__":
    main()
