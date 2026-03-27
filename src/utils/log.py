"""Utility functions for logging configuration."""

import logging
import sys


def setup_logging(level: str) -> None:
    """Sets up structured JSON logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    fmt = '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
