import pytest

from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import ClosedState, Context, OpenedState
from tests.unittests.time import AsyncSleep


def test_circuitbreaker_open_raise():
    context = Context("my", threshold=2, ttl=42)
    context.set_state(OpenedState("my"))
    count = 0
    with pytest.raises(OpenedState):
        with context:
            count += 1
    assert count == 0
    assert context.messages == [
        ContextChanged(name="my", state="opened", opened_at=context.opened_at),
    ]


async def test_circuitbreaker_open_closed_after_ttl_passed():
    context = Context("my", threshold=5, ttl=0.1)
    state = OpenedState("my")
    context.set_state(state)
    assert context.messages == [
        ContextChanged(name="my", state="opened", opened_at=state.opened_at),
    ]
    context.messages.clear()
    await AsyncSleep(0.1)

    count = 0
    with context:
        count += 1
    assert count == 1
    assert context.messages == [
        ContextChanged(name="my", state="half-opened", opened_at=None),
        CircuitBreakerRecovered(name="my"),
        ContextChanged(name="my", state="closed", opened_at=None),
    ]
    assert context._state == ClosedState()


async def test_circuitbreaker_open_reopened_after_ttl_passed():
    context = Context("my", threshold=5, ttl=0.1)
    state = OpenedState("my")
    context.set_state(state)
    await AsyncSleep(0.1)

    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert context.messages == [
        ContextChanged(name="my", state="opened", opened_at=state.opened_at),
        ContextChanged(name="my", state="half-opened", opened_at=None),
        ContextChanged(name="my", state="opened", opened_at=context.opened_at),
    ]
    state = OpenedState("my")
    state.opened_at = context.opened_at or 0
    assert context._state == state


def test_circuitbreaker_closed_state_opening():
    context = Context("my", threshold=2, ttl=1)
    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert context.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    context.messages.clear()

    state = ClosedState()
    state.failure_count = 1
    assert context._state == state
    assert context.failure_count == 1

    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert context.messages == [
        CircuitBreakerFailed(name="my", failure_count=2),
        ContextChanged(name="my", state="opened", opened_at=context.opened_at),
    ]
    state = OpenedState("my")
    state.opened_at = context.opened_at or 0
    assert context._state == state


def test_circuitbreaker_reset_after_failure():
    context = Context("my", threshold=5, ttl=1)
    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert context.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert context.failure_count == 1
    context.messages.clear()
    with context:
        pass

    assert context.messages == [CircuitBreakerRecovered(name="my")]


def test_circuitbreaker_can_exclude_exception():
    class MyException(RuntimeError):
        pass

    context = Context("my", threshold=5, ttl=1, exclude=[MyException])
    try:
        with context:
            raise MyException("Boom")
    except MyException:
        pass

    assert context.messages == []
    assert context.failure_count == 0

    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert context.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert context.failure_count == 1
    context.messages.clear()

    try:
        with context:
            raise MyException("Boom")
    except MyException:
        pass

    assert context.messages == [CircuitBreakerRecovered(name="my")]
    assert context.failure_count == 0


def test_circuitbreaker_can_exclude_function():
    class HTTPError(Exception):
        def __init__(self, status_code) -> None:
            super().__init__(f"{status_code} Error")
            self.status_code = status_code

    context = Context(
        "my",
        threshold=5,
        ttl=1,
        exclude=[(HTTPError, lambda exc: exc.status_code < 500)],
    )
    try:
        with context:
            raise HTTPError(503)
    except HTTPError:
        pass

    assert context.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert context.failure_count == 1
    context.messages.clear()

    try:
        with context:
            raise HTTPError(404)
    except HTTPError:
        pass

    assert context.messages == [CircuitBreakerRecovered(name="my")]
    assert context.failure_count == 0
    context.messages.clear()

    try:
        with context:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    assert context.messages == [CircuitBreakerFailed(name="my", failure_count=1)]
    assert context.failure_count == 1
