"""Per-client request rate limiting, kept in process memory.

Sliding window per (scope, client IP). In memory rather than in Postgres or
Redis: one uvicorn worker serves the whole app, so one process sees every
request, and a restart forgetting the counters is harmless. With several
workers each would count separately (limits multiplied by the worker count)
— revisit then.

The client IP is request.client.host: behind Caddy, uvicorn rewrites it
from X-Forwarded-For (FORWARDED_ALLOW_IPS in docker-compose.prod.yml).
"""

import time
from collections import deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

TOO_MANY_REQUESTS_MESSAGE = "Trop de tentatives. Réessayez dans quelques minutes."
# Past this many tracked keys, idle ones are swept, so a flood of distinct
# IPs can't grow the dict forever.
_SWEEP_THRESHOLD = 10_000


class RateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """Records a hit for `key` and says whether it is within the limit.
        Refused hits are not recorded, so hammering doesn't extend the wait."""
        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            if len(self._hits) > _SWEEP_THRESHOLD:
                self._sweep(cutoff)
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            return True

    def _sweep(self, cutoff: float) -> None:
        idle = [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in idle:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Limits per client IP. Login is the brute-force / credential-stuffing
# target; signup and reset requests are cheap to spam (bcrypt hashing, log
# lines); account changes guard the current-password check against a
# stolen session; suggestions are the CPU-heavy public endpoint (embedding
# + matching).
LOGIN_LIMITER = RateLimiter(max_requests=10, window_seconds=5 * 60)
SIGNUP_LIMITER = RateLimiter(max_requests=5, window_seconds=60 * 60)
PASSWORD_RESET_LIMITER = RateLimiter(max_requests=5, window_seconds=60 * 60)
ACCOUNT_UPDATE_LIMITER = RateLimiter(max_requests=10, window_seconds=5 * 60)
SUGGESTIONS_LIMITER = RateLimiter(max_requests=30, window_seconds=60)

ALL_LIMITERS = (
    LOGIN_LIMITER,
    SIGNUP_LIMITER,
    PASSWORD_RESET_LIMITER,
    ACCOUNT_UPDATE_LIMITER,
    SUGGESTIONS_LIMITER,
)


def reset_all() -> None:
    for limiter in ALL_LIMITERS:
        limiter.reset()


def limit(limiter: RateLimiter) -> Callable[[Request], None]:
    """A FastAPI dependency answering 429 once the caller's IP is over
    `limiter`'s budget: `dependencies=[Depends(limit(LOGIN_LIMITER))]`."""

    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        if not limiter.allow(client_ip):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                TOO_MANY_REQUESTS_MESSAGE,
                headers={"Retry-After": str(int(limiter.window_seconds))},
            )

    return dependency
