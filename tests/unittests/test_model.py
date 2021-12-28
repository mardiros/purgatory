import asyncio
from typing import cast

import pytest

from purgatory.domain.model import CircuitBreaker, ClosedState, OpenedState


@pytest.mark.asyncio
async def test_circuitbreaker_open_raise():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=42)
    circuitbreaker.set_state(OpenedState())
    circuitbreaker._dirty = False
    count = 0
    with pytest.raises(OpenedState):
        with circuitbreaker:
            count += 1
    assert count == 0
    assert circuitbreaker.dirty is False


@pytest.mark.asyncio
async def test_circuitbreaker_open_closed_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    circuitbreaker.set_state(OpenedState())
    await asyncio.sleep(0.1)

    count = 0
    with circuitbreaker:
        count += 1
    assert count == 1
    assert circuitbreaker.dirty is True
    assert circuitbreaker._state == ClosedState()


@pytest.mark.asyncio
async def test_circuitbreaker_open_reopened_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    circuitbreaker.set_state(OpenedState())
    await asyncio.sleep(0.1)

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert circuitbreaker.dirty is True
    assert circuitbreaker._state == OpenedState()


@pytest.mark.asyncio
async def test_circuitbreaker_closed_state_opening():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=1)
    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert not circuitbreaker.dirty
    assert circuitbreaker._state == ClosedState()
    assert cast(ClosedState, circuitbreaker._state).failure_count == 1

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker.dirty is True
    assert circuitbreaker._state == OpenedState()
