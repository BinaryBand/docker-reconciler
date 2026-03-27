import json
import logging
import sys


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # Simple structured logging example
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        json.dumps(
            {"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}
        )
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
