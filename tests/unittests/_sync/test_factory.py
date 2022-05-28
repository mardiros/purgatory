from typing import cast

from purgatory.domain.model import Context
from purgatory.service._sync.repository import SyncInMemoryRepository


def test_circuitbreaker_factory_context(circuitbreaker):

    count = 0

    with circuitbreaker.get_breaker("my"):
        count += 1

    with circuitbreaker.get_breaker("my2", threshold=42, ttl=42):
        count += 1

    with circuitbreaker.get_breaker("my", exclude=[ValueError]):
        count += 1

    assert count == 3
    assert (circuitbreaker.get_breaker("my")).context.messages == []
    assert cast(SyncInMemoryRepository, circuitbreaker.uow.contexts).breakers == {
        "my": Context(name="my", threshold=5, ttl=30),
        "my2": Context(name="my2", threshold=42, ttl=42),
    }


def test_circuitbreaker_factory_context_exclude_exceptions_with_context(
    circuitbreaker,
):
    cbr = circuitbreaker.get_breaker("my", threshold=1, exclude=[ValueError])
    try:
        with cbr:
            raise ValueError(42)
    except ValueError:
        pass
    assert cbr.context._state.failure_count == 0
    assert cbr.context.state == "closed"

    try:
        with circuitbreaker.get_breaker("my", exclude=[RuntimeError]):
            raise ValueError(42)
    except ValueError:
        pass
    assert cbr.context.state == "opened"


def test_circuitbreaker_factory_context_exclude_exceptions_with_decorator(
    circuitbreaker,
):
    @circuitbreaker("my", threshold=1, exclude=[ValueError])
    def raise_error(typ_: str):
        if typ_ == "value":
            raise ValueError(42)
        raise RuntimeError("boom")

    try:
        raise_error("value")
    except ValueError:
        pass

    assert (circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        raise_error("runtime")
    except RuntimeError:
        pass

    assert (circuitbreaker.get_breaker("my")).context.state == "opened"
