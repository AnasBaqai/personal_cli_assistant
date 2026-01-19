"""Logging configuration for the CLI assistant."""

import logging
import sys
from typing import TextIO


def get_logger(
    name: str,
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level
        stream: Output stream for logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        handler = logging.StreamHandler(stream)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def configure_debug_logging() -> None:
    """Enable debug logging for all assistant modules."""
    logging.getLogger("src").setLevel(logging.DEBUG)


def configure_quiet_logging() -> None:
    """Disable most logging output."""
    logging.getLogger("src").setLevel(logging.ERROR)
