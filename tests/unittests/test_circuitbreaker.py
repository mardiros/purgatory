from dataclasses import asdict
from typing import cast

import pytest
from purgatory.domain.messages.events import CircuitBreakerStateChanged

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.repository import InMemoryRepository


@pytest.mark.asyncio
async def test_circuitbreaker_factory_decorator(circuitbreaker):

    count = 0

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
async def test_circuitbreaker_factory_context(circuitbreaker):

    count = 0

    async with await circuitbreaker.get_breaker("my"):
        count += 1

    async with await circuitbreaker.get_breaker("my2", threshold=42, ttl=42):
        count += 1

    assert (await circuitbreaker.get_breaker("my")).brk.dirty is False
    assert cast(InMemoryRepository, circuitbreaker.uow.circuit_breakers).breakers == {
        "my": CircuitBreaker(name="my", threshold=5, ttl=300),
        "my2": CircuitBreaker(name="my2", threshold=42, ttl=42),
    }


@pytest.mark.asyncio
async def test_circuitbreaker_raise_state_changed_event(circuitbreaker):

    evts = []

    async def evt_handler(cmd: CircuitBreakerStateChanged, uow):
        evts.append(asdict(cmd))

    circuitbreaker.messagebus.add_listener(CircuitBreakerStateChanged, evt_handler)
    brk = await circuitbreaker.get_breaker("my", threshold=2)
    try:
        async with brk:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert evts == []

    try:
        async with brk:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert evts == [
        {
            "name": "my",
            "opened_at": evts[0]["opened_at"],
            "state": "OpenedState",
        },
    ]

    assert (await circuitbreaker.get_breaker("my")).brk.dirty is True
