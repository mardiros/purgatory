import asyncio
from typing import cast
import pytest
from aiobreak.domain.repository import InMemoryRepository

from aiobreak.service.circuitbreaker import CircuitBreaker, CircuitBreakerFactory
from aiobreak.domain.model import OpenedState, ClosedState
from aiobreak.service.unit_of_work import InMemoryUnitOfWork


@pytest.mark.asyncio
async def test_circuitbreaker_factory_decorator():

    count = 0
    circuitbreaker = CircuitBreakerFactory()

    @circuitbreaker(circuit="client")
    async def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1

    await fail_or_success()
    assert count == 1

    with pytest.raises(RuntimeError):
        await fail_or_success(fail=True)

    brk = await circuitbreaker.uow.circuit_breakers.get("client")
    assert brk == CircuitBreaker(name="client", threshold=5, ttl=300)
    # assert circuitbreaker.breakers["client"]._state._state.failure_count == 1

    @circuitbreaker(circuit="client2", threshold=15)
    async def _success2():
        pass
    await _success2()
    brk = await circuitbreaker.uow.circuit_breakers.get("client2")
    assert brk == CircuitBreaker(name="client2", threshold=15, ttl=300)

    @circuitbreaker(circuit="client3", ttl=60)
    async def _success3():
        pass

    await _success3()
    brk = await circuitbreaker.uow.circuit_breakers.get("client3")
    assert brk == CircuitBreaker(name="client3", threshold=5, ttl=60)


def test_circuitbreaker_state():
    circuitbreaker = CircuitBreaker("plop", 5, 30)
    assert (
        repr(circuitbreaker)
        == '<CircuitBreaker name="plop" state="ClosedState" threshold="5" ttl="30">'
    )


@pytest.mark.asyncio
async def test_circuitbreaker_factory_context():

    count = 0
    circuitbreaker = CircuitBreakerFactory()

    async with await circuitbreaker.get_breaker("my"):
        count += 1

    async with await circuitbreaker.get_breaker("my2", threshold=42, ttl=42):
        count += 1

    assert cast(InMemoryRepository, circuitbreaker.uow.circuit_breakers).breakers == {
        "my": CircuitBreaker(name="my", threshold=5, ttl=300),
        "my2": CircuitBreaker(name="my2", threshold=42, ttl=42),
    }


@pytest.mark.asyncio
async def test_circuitbreaker_open_raise():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=42)
    circuitbreaker.set_state(OpenedState())

    count = 0
    with pytest.raises(OpenedState):
        async with circuitbreaker:
            count += 1
    assert count == 0


@pytest.mark.asyncio
async def test_circuitbreaker_open_closed_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    circuitbreaker.set_state(OpenedState())
    await asyncio.sleep(0.1)

    count = 0
    async with circuitbreaker:
        count += 1
    assert count == 1
    assert circuitbreaker._state == ClosedState()


@pytest.mark.asyncio
async def test_circuitbreaker_open_reopened_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    circuitbreaker.set_state(OpenedState())
    await asyncio.sleep(0.1)

    try:
        async with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert circuitbreaker._state == OpenedState()


@pytest.mark.asyncio
async def test_circuitbreaker_closed_state_opening():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=1)
    circuitbreaker.set_state(ClosedState())
    try:
        async with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert circuitbreaker._state == ClosedState()
    assert circuitbreaker._state.failure_count == 1

    try:
        async with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker._state == OpenedState()
