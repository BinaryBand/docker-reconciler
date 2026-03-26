"""Run the dev container verification sequence against the local workspace."""

import subprocess
import sys
from pathlib import Path

_IMAGE = "mcr.microsoft.com/devcontainers/python:3.11-bookworm"
_WORKSPACE = Path(__file__).resolve().parent.parent
_VENV = "/tmp/.venv"

_STEPS = " && ".join([
    f"python -m venv {_VENV}",
    f"{_VENV}/bin/pip install -e '.[dev]' -q",
    f"{_VENV}/bin/pytest -v",
    f"{_VENV}/bin/ruff check src/",
    f"{_VENV}/bin/pyright src/ --pythonpath {_VENV}/bin/python",
    f"{_VENV}/bin/python -m src.main",
    "echo '=== ALL CHECKS PASSED ==='",
])


def main() -> None:
    """Build and verify the dev container environment locally."""
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{_WORKSPACE}:/workspace",
            "-w", "/workspace",
            _IMAGE, "bash", "-c", _STEPS,
        ],
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()