from __future__ import annotations

import json
import time

from .config import RATE_LIMIT

_request_count = {"second": 0, "month": 0, "last_reset": time.monotonic()}


def check_rate_limit() -> None:
    # TODO: Improve rate-limit logic to support self-throttling and n-keys
    now = time.monotonic()
    if now - _request_count["last_reset"] > 1.0:
        _request_count["second"] = 0
        _request_count["last_reset"] = now
    if (
        _request_count["second"] >= RATE_LIMIT["per_second"]
        or _request_count["month"] >= RATE_LIMIT["per_month"]
    ):
        raise RuntimeError("Rate limit exceeded")
    _request_count["second"] += 1
    _request_count["month"] += 1


def stringify(data: object, pretty: bool = False) -> str:
    return json.dumps(data, indent=2) if pretty else json.dumps(data)
