import subprocess
import sys
from pathlib import Path

# Resolve paths relative to the project root (one level up from this script)
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
    """Provision permissions and start up the docker project."""
    run_command(
        [
            str(VENV_BIN / "ansible-playbook"),
            "-i",
            "ansible/inventory/hosts",
            "ansible/playbooks/provision.yml",
            "--ask-become-pass",
        ]
    )
    run_command(["docker", "compose", "up", "-d", "--build"])
    print("Docker project started successfully!")


if __name__ == "__main__":
    main()
