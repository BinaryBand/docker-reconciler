"""Command execution utilities — maps state labels to subprocess commands."""

import subprocess

from src.models.state import StateLabel

_COMMANDS: dict[StateLabel, list[str]] = {
    StateLabel.T1: [
        "ansible-playbook",
        "-i",
        "ansible/inventory/hosts",
        "ansible/playbooks/provision.yml",
        "--tags",
        "volumes",
    ],
    StateLabel.T2: [
        "ansible-playbook",
        "-i",
        "ansible/inventory/hosts",
        "ansible/playbooks/provision.yml",
        "--tags",
        "permissions",
    ],
    StateLabel.T3: ["docker", "compose", "up", "-d"],
}


def run_command(state: StateLabel) -> None:
    """Issue the subprocess command that advances the system toward the given state.

    States without a mapped command (T0, T4, T5) are intentional no-ops —
    they represent observed conditions rather than imperative actions.
    """
    cmd = _COMMANDS.get(state)
    if cmd:
        subprocess.run(cmd, check=True)
