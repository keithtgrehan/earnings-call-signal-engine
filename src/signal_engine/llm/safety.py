from __future__ import annotations

import re
from typing import Any

SECRET_PATTERN = re.compile(r"\b(?:sk|pk|ak)-[A-Za-z0-9._\-]{6,}\b")


def redact_secret_values(text: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", text)


def contains_secret_like_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return SECRET_PATTERN.search(value) is not None
