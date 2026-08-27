"""Stdlib step logging for MAF slices.

Logs go to stderr so JSON on stdout stays parseable. Set ``MAF_LOG=DEBUG``
for extra fields (missing list, truncated answers). Default is INFO.
"""

from __future__ import annotations

import logging
import os
import sys

LOGGER = logging.getLogger("maf")
_CONFIGURED = False


def setup() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    name = os.environ.get("MAF_LOG", "INFO").upper()
    level = getattr(logging, name, logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    )
    LOGGER.setLevel(level)
    LOGGER.addHandler(handler)
    LOGGER.propagate = False
    _CONFIGURED = True


def step(node: str, **fields: object) -> None:
    LOGGER.info("%s%s", node, _suffix(fields))


def debug(node: str, **fields: object) -> None:
    LOGGER.debug("%s%s", node, _suffix(fields))


def warn(node: str, **fields: object) -> None:
    LOGGER.warning("%s%s", node, _suffix(fields))


def _suffix(fields: dict[str, object]) -> str:
    parts = [f"{key}={_fmt(value)}" for key, value in fields.items() if value is not None]
    return f" {' '.join(parts)}" if parts else ""


def _fmt(value: object) -> str:
    if isinstance(value, str) and len(value) > 96:
        return repr(value[:93] + "...")
    return repr(value)
