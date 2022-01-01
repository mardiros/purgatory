from typing import cast

import pytest

from purgatory.domain.model import Context
from purgatory.domain.repository import InMemoryRepository


@pytest.mark.asyncio
async def test_circuitbreaker_factory_context(circuitbreaker):

    count = 0

    async with await circuitbreaker.get_breaker("my"):
        count += 1

    async with await circuitbreaker.get_breaker("my2", threshold=42, ttl=42):
        count += 1

    async with await circuitbreaker.get_breaker("my", exclude=[ValueError]):
        count += 1

    assert count == 3
    assert (await circuitbreaker.get_breaker("my")).context.messages == []
    assert cast(InMemoryRepository, circuitbreaker.uow.contexts).breakers == {
        "my": Context(name="my", threshold=5, ttl=30),
        "my2": Context(name="my2", threshold=42, ttl=42),
    }


@pytest.mark.asyncio
async def test_circuitbreaker_factory_context_exclude_exceptions_with_context(
    circuitbreaker,
):
    cbr = await circuitbreaker.get_breaker("my", threshold=1, exclude=[ValueError])
    try:
        async with cbr:
            raise ValueError(42)
    except ValueError:
        pass
    assert cbr.context._state.failure_count == 0
    assert cbr.context.state == "closed"

    try:
        async with await circuitbreaker.get_breaker("my", exclude=[RuntimeError]):
            raise ValueError(42)
    except ValueError:
        pass
    assert cbr.context.state == "opened"


@pytest.mark.asyncio
async def test_circuitbreaker_factory_context_exclude_exceptions_with_decorator(
    circuitbreaker,
):
    @circuitbreaker("my", threshold=1, exclude=[ValueError])
    async def raise_error(typ_: str):
        if typ_ == "value":
            raise ValueError(42)
        raise RuntimeError("boom")

    try:
        await raise_error("value")
    except ValueError:
        pass

    assert (await circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (await circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        await raise_error("runtime")
    except RuntimeError:
        pass

    assert (await circuitbreaker.get_breaker("my")).context.state == "opened"
