"""Shared type narrowing utilities."""

from typing import TypeGuard, cast


def is_str_dict(value: object) -> TypeGuard[dict[str, object]]:
    """Return True if value is a dict with only string keys."""
    if not isinstance(value, dict):
        return False
    return all(isinstance(k, str) for k in cast(dict[object, object], value))
