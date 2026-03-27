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
    """Tear down the docker project."""
    run_command(["docker", "compose", "down"])
    print("Docker project stopped and removed successfully!")


if __name__ == "__main__":
    main()
