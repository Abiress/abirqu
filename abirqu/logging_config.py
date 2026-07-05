"""
AbirQu Logging Configuration
=============================
Centralized logging setup with sensible defaults for production use.
"""
from __future__ import annotations

import logging
import sys


_DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str | int = "INFO",
    fmt: str | None = None,
    datefmt: str | None = None,
    stream: object | None = None,
) -> None:
    """Configure the root logger for the entire AbirQu package.

    Parameters
    ----------
    level : str or int
        Logging level (e.g. ``"DEBUG"``, ``"INFO"``, ``"WARNING"``).
    fmt : str, optional
        Override the log format string.
    datefmt : str, optional
        Override the date format string.
    stream : file-like, optional
        Override the output stream (defaults to ``sys.stderr``).
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        fmt or _DEFAULT_FORMAT,
        datefmt or _DEFAULT_DATEFMT,
    ))

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates on repeated calls.
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
