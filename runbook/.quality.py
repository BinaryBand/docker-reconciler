import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_BIN = PROJECT_ROOT / ".venv" / "bin"


def run_command(command: list[str]) -> None:
    """Run a shell command and exit if it fails."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=False, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def main() -> None:
    """Run all quality checks."""
    commands = [
        [str(VENV_BIN / "pyright"), "src/"],
        [str(VENV_BIN / "ruff"), "check", "src/"],
        [str(VENV_BIN / "ruff"), "format", "src/", "--check"],
        [str(VENV_BIN / "lizard"), "src/", "-C", "5", "-L", "25", "-a", "4"],
        [str(VENV_BIN / "lint-imports")],
    ]

    for cmd in commands:
        run_command(cmd)

    print("All quality checks passed!")


if __name__ == "__main__":
    main()
