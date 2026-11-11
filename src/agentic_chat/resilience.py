"""Bound provider work and stop repeated failures without retry amplification."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class ProviderUnavailable(Exception):
    """Only an application-owned reason code may cross the provider boundary."""


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        cooldown: float = 30,
        timeout: float = 20,
        slow_after: float | None = None,
        max_in_flight: int = 4,
        clock: Callable[[], float] = time.monotonic,
    ):
        if min(failure_threshold, cooldown, timeout, max_in_flight) <= 0:
            raise ValueError("Circuit limits must be positive")
        self.threshold = failure_threshold
        self.cooldown = cooldown
        self.timeout = timeout
        self.slow_after = timeout if slow_after is None else slow_after
        self.capacity = max_in_flight
        self.clock = clock
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0
        self.in_flight = 0
        self._epoch = 0

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        # Admission has no await: one event loop cannot interleave the check and increment.
        if self.state == "open":
            if self.clock() - self.opened_at < self.cooldown:
                raise ProviderUnavailable("circuit_open")
            self.state = "half_open"
        elif self.state == "half_open":
            raise ProviderUnavailable("circuit_open")
        if self.in_flight >= self.capacity:
            if self.state == "half_open":
                self.state = "open"
            raise ProviderUnavailable("provider_busy")
        probe = self.state == "half_open"
        epoch = self._epoch
        self.in_flight += 1
        started = self.clock()
        try:
            async with asyncio.timeout(self.timeout):
                result = await operation()
            if self.clock() - started > self.slow_after:
                raise ProviderUnavailable("slow_call")
        except asyncio.CancelledError:
            if probe:
                self._open()
            raise
        except Exception as error:
            if epoch == self._epoch:
                self.failures += 1
                if probe or self.failures >= self.threshold:
                    self._open()
            code = "timeout" if isinstance(error, TimeoutError) else "provider_failure"
            if getattr(error, "code", None) in {"credit_balance_exhausted", "insufficient_quota"}:
                code = "provider_quota_exhausted"
            elif getattr(error, "status_code", None) == 429:
                code = "provider_rate_limited"
            elif getattr(error, "status_code", None) in {401, 403}:
                code = "provider_authentication_failed"
            if isinstance(error, ProviderUnavailable):
                code = str(error)
            raise ProviderUnavailable(code) from None
        else:
            # A response started before a trip must not close the newer circuit.
            if epoch == self._epoch:
                self.failures = 0
                self.state = "closed"
            return result
        finally:
            self.in_flight -= 1

    def _open(self):
        self.state = "open"
        self.opened_at = self.clock()
        self._epoch += 1
