from __future__ import annotations

import os
from typing import Iterable


def _missing(keys: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for key in keys:
        value = os.getenv(key, "").strip()
        if not value:
            missing.append(key)
    return missing


def validate_required_env(required_keys: Iterable[str]) -> list[str]:
    """Raise ValueError if any required key is missing. Returns list when complete."""
    missing = _missing(required_keys)
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    return []


def validate_optional_env(optional_keys: Iterable[str]) -> list[str]:
    """Return optional keys that are currently missing."""
    return _missing(optional_keys)
