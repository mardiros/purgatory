import asyncio

import pytest

from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    CircuitBreakerStateChanged,
)
from purgatory.domain.model import CircuitBreaker, ClosedState, OpenedState


def test_circuitbreaker_open_raise():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=42)
    circuitbreaker.set_state(OpenedState())
    count = 0
    with pytest.raises(OpenedState):
        with circuitbreaker:
            count += 1
    assert count == 0
    assert circuitbreaker.messages == [
        CircuitBreakerStateChanged(
            name="my", state="opened", opened_at=circuitbreaker.opened_at
        ),
    ]


@pytest.mark.asyncio
async def test_circuitbreaker_open_closed_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    state = OpenedState()
    circuitbreaker.set_state(state)
    assert circuitbreaker.messages == [
        CircuitBreakerStateChanged(
            name="my", state="opened", opened_at=state.opened_at
        ),
    ]
    circuitbreaker.messages.clear()
    await asyncio.sleep(0.1)

    count = 0
    with circuitbreaker:
        count += 1
    assert count == 1
    assert circuitbreaker.messages == [
        CircuitBreakerStateChanged(name="my", state="half-opened", opened_at=None),
        CircuitBreakerRecovered(name="my"),
        CircuitBreakerStateChanged(name="my", state="closed", opened_at=None),
    ]
    assert circuitbreaker._state == ClosedState()


@pytest.mark.asyncio
async def test_circuitbreaker_open_reopened_after_ttl_passed():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=0.1)
    state = OpenedState()
    circuitbreaker.set_state(state)
    await asyncio.sleep(0.1)

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert circuitbreaker.messages == [
        CircuitBreakerStateChanged(
            name="my", state="opened", opened_at=state.opened_at
        ),
        CircuitBreakerStateChanged(name="my", state="half-opened", opened_at=None),
        CircuitBreakerRecovered(name="my"),
        CircuitBreakerStateChanged(
            name="my", state="opened", opened_at=circuitbreaker.opened_at
        ),
    ]
    state = OpenedState()
    state.opened_at = circuitbreaker.opened_at or 0
    assert circuitbreaker._state == state


def test_circuitbreaker_closed_state_opening():
    circuitbreaker = CircuitBreaker("my", threshold=2, ttl=1)
    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert circuitbreaker.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    circuitbreaker.messages.clear()

    state = ClosedState()
    state.failure_count = 1
    assert circuitbreaker._state == state
    assert circuitbreaker.failure_count == 1

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker.messages == [
        CircuitBreakerStateChanged(
            name="my", state="opened", opened_at=circuitbreaker.opened_at
        ),
    ]
    state = OpenedState()
    state.opened_at = circuitbreaker.opened_at or 0
    assert circuitbreaker._state == state


def test_circuitbreaker_reset_after_failure():
    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=1)
    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert circuitbreaker.failure_count == 1
    circuitbreaker.messages.clear()
    with circuitbreaker:
        pass

    assert circuitbreaker.messages == [CircuitBreakerRecovered(name="my")]


@pytest.mark.asyncio
def test_circuitbreaker_can_exclude_exception():
    class MyException(RuntimeError):
        pass

    circuitbreaker = CircuitBreaker("my", threshold=5, ttl=1, exclude=[MyException])
    try:
        with circuitbreaker:
            raise MyException("Boom")
    except MyException:
        pass

    assert circuitbreaker.messages == []
    assert circuitbreaker.failure_count == 0

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert circuitbreaker.failure_count == 1
    circuitbreaker.messages.clear()

    try:
        with circuitbreaker:
            raise MyException("Boom")
    except MyException:
        pass

    assert circuitbreaker.messages == [CircuitBreakerRecovered(name="my")]
    assert circuitbreaker.failure_count == 0


@pytest.mark.asyncio
def test_circuitbreaker_can_exclude_function():
    class HTTPError(Exception):
        def __init__(self, status_code) -> None:
            super().__init__(f"{status_code} Error")
            self.status_code = status_code

    circuitbreaker = CircuitBreaker(
        "my",
        threshold=5,
        ttl=1,
        exclude=[(HTTPError, lambda exc: exc.status_code < 500)],
    )
    try:
        with circuitbreaker:
            raise HTTPError(503)
    except HTTPError:
        pass

    assert circuitbreaker.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert circuitbreaker.failure_count == 1
    circuitbreaker.messages.clear()

    try:
        with circuitbreaker:
            raise HTTPError(404)
    except HTTPError:
        pass

    assert circuitbreaker.messages == [CircuitBreakerRecovered(name="my")]
    assert circuitbreaker.failure_count == 0
    circuitbreaker.messages.clear()

    try:
        with circuitbreaker:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert circuitbreaker.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert circuitbreaker.failure_count == 1
