import subprocess
import sys


def run_command(command: list[str]) -> None:
    """Run a shell command and exit if it fails."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=False)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def main() -> None:
    """Run all quality checks."""
    commands = [
        ["pyright", "src/"],
        ["ruff", "check", "src/"],
        ["ruff", "format", "src/", "--check"],
        ["lizard", "src/", "-C", "5", "-L", "25", "-a", "4"],
        ["lint-imports"],
    ]

    for cmd in commands:
        run_command(cmd)

    print("All quality checks passed!")


if __name__ == "__main__":
    main()
