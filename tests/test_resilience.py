import asyncio

import pytest

from agentic_chat.resilience import CircuitBreaker, ProviderUnavailable


def test_open_circuit_stops_calls_and_recovers_with_one_probe():
    async def scenario():
        now = [0.0]
        circuit = CircuitBreaker(failure_threshold=2, cooldown=10, clock=lambda: now[0])
        calls = 0

        async def failing():
            nonlocal calls
            calls += 1
            raise RuntimeError("private provider error")

        for _ in range(2):
            with pytest.raises(ProviderUnavailable):
                await circuit.call(failing)
        with pytest.raises(ProviderUnavailable, match="circuit_open"):
            await circuit.call(failing)
        assert calls == 2
        now[0] = 11

        async def healthy():
            return "ok"

        assert await circuit.call(healthy) == "ok"
        assert circuit.state == "closed"

    asyncio.run(scenario())


def test_only_one_half_open_probe_is_admitted():
    async def scenario():
        now = [0.0]
        circuit = CircuitBreaker(failure_threshold=1, cooldown=1, clock=lambda: now[0])

        async def fail():
            raise RuntimeError()

        with pytest.raises(ProviderUnavailable):
            await circuit.call(fail)
        now[0] = 2
        started, release = asyncio.Event(), asyncio.Event()

        async def probe():
            started.set()
            await release.wait()
            return "recovered"

        task = asyncio.create_task(circuit.call(probe))
        await started.wait()
        with pytest.raises(ProviderUnavailable, match="circuit_open"):
            await circuit.call(probe)
        release.set()
        assert await task == "recovered"
        assert circuit.state == "closed"

    asyncio.run(scenario())


def test_late_success_cannot_close_a_newly_opened_circuit():
    async def scenario():
        circuit = CircuitBreaker(failure_threshold=1)
        started, release = asyncio.Event(), asyncio.Event()

        async def slow_success():
            started.set()
            await release.wait()
            return "late"

        async def fail():
            raise RuntimeError()

        task = asyncio.create_task(circuit.call(slow_success))
        await started.wait()
        with pytest.raises(ProviderUnavailable):
            await circuit.call(fail)
        release.set()
        await task
        assert circuit.state == "open"

    asyncio.run(scenario())


def test_slow_completed_calls_trip_breaker_and_are_discarded():
    async def scenario():
        now = [0.0]
        circuit = CircuitBreaker(failure_threshold=1, slow_after=1, clock=lambda: now[0])

        async def slow():
            now[0] = 2
            return "late answer"

        with pytest.raises(ProviderUnavailable, match="slow_call"):
            await circuit.call(slow)
        assert circuit.state == "open"

    asyncio.run(scenario())


def test_provider_bulkhead_rejects_excess_work_without_calling_provider():
    async def scenario():
        circuit = CircuitBreaker(max_in_flight=1)
        started, release = asyncio.Event(), asyncio.Event()

        async def waiting():
            started.set()
            await release.wait()

        task = asyncio.create_task(circuit.call(waiting))
        await started.wait()
        with pytest.raises(ProviderUnavailable, match="provider_busy"):
            await circuit.call(waiting)
        release.set()
        await task
        assert circuit.in_flight == 0
        assert circuit.failures == 0

    asyncio.run(scenario())


def test_deadline_cancels_slow_call_and_releases_capacity():
    async def scenario():
        cancelled = asyncio.Event()
        circuit = CircuitBreaker(timeout=0.01, failure_threshold=1)

        async def slow():
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.set()

        with pytest.raises(ProviderUnavailable, match="timeout"):
            await circuit.call(slow)
        assert cancelled.is_set()
        assert circuit.in_flight == 0
        assert circuit.state == "open"

    asyncio.run(scenario())
