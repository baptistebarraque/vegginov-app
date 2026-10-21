import pytest

from veggie_app.services import rate_limit_service
from veggie_app.services.rate_limit_service import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_refuses() -> None:
    limiter = RateLimiter(max_requests=3, window_seconds=60, clock=FakeClock())

    results = [limiter.allow("1.2.3.4") for _ in range(4)]

    assert results == [True, True, True, False]


def test_counts_each_client_separately() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=FakeClock())

    assert limiter.allow("1.1.1.1") is True
    assert limiter.allow("2.2.2.2") is True
    assert limiter.allow("1.1.1.1") is False


def test_window_slides_so_old_hits_expire() -> None:
    clock = FakeClock()
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    limiter.allow("ip")
    clock.now += 30
    limiter.allow("ip")

    clock.now += 31  # the first hit is now older than 60 s
    assert limiter.allow("ip") is True
    assert limiter.allow("ip") is False


def test_refused_hits_do_not_extend_the_wait() -> None:
    clock = FakeClock()
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=clock)
    limiter.allow("ip")
    for _ in range(50):
        clock.now += 1
        limiter.allow("ip")

    clock.now += 10  # 60 s after the only recorded hit
    assert limiter.allow("ip") is True


def test_idle_clients_are_swept_once_many_are_tracked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit_service, "_SWEEP_THRESHOLD", 3)
    clock = FakeClock()
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=clock)
    for ip in ("a", "b", "c", "d"):
        limiter.allow(ip)

    clock.now += 61
    limiter.allow("e")

    assert set(limiter._hits) == {"e"}


def test_reset_forgets_everything() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=FakeClock())
    limiter.allow("ip")

    limiter.reset()

    assert limiter.allow("ip") is True
