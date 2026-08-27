"""Rate limiting (SECURITY.md) — slowapi shared limiter.

Rate limits apply by default; the load-test instance disables them
(NETRA_RATE_LIMIT_ENABLED=false) so the burst measures the pipeline,
not the 429 guard (guard behavior is covered by tests/test_security.py).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address)


def limit(rate: str):
    def deco(fn):
        if settings.rate_limit_enabled:
            return limiter.limit(rate)(fn)
        return fn

    return deco