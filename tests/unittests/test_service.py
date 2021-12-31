import asyncio
from dataclasses import asdict
from typing import cast

import pytest

from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context
from purgatory.domain.repository import InMemoryRepository
from purgatory.service.circuitbreaker import CircuitBreakerFactory
from tests.unittests.conftest import FakeRedis


@pytest.mark.asyncio
async def test_circuitbreaker_factory_decorator(circuitbreaker: CircuitBreakerFactory):

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
    assert brk == Context(name="client", threshold=5, ttl=30)
    # assert circuitbreaker.breakers["client"]._state._state.failure_count == 1

    @circuitbreaker(circuit="client2", threshold=15)
    async def _success2():
        pass

    await _success2()
    brk = await circuitbreaker.uow.circuit_breakers.get("client2")
    assert brk == Context(name="client2", threshold=15, ttl=30)

    @circuitbreaker(circuit="client3", ttl=60)
    async def _success3():
        pass

    await _success3()
    brk = await circuitbreaker.uow.circuit_breakers.get("client3")
    assert brk == Context(name="client3", threshold=5, ttl=60)


@pytest.mark.asyncio
async def test_redis_circuitbreaker_factory_decorator(
    fake_redis: FakeRedis, circuitbreaker_redis: CircuitBreakerFactory
):

    count = 0
    await circuitbreaker_redis.initialize()

    @circuitbreaker_redis(circuit="client", threshold=3, ttl=0.1)
    async def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1

    async def fail():
        try:
            await fail_or_success(True)
        except RuntimeError:
            pass

    await fail()
    await fail()

    assert fake_redis.deserialized_storage == {
        "cbr::client": {
            "name": "client",
            "opened_at": None,
            "state": "closed",
            "threshold": 3,
            "ttl": 0.1,
        },
        "cbr::client::failure_count": 2,
    }

    await fail_or_success(fail=False)
    await fail()


@pytest.mark.parametrize("uow", ["inmemory", "redis"])
@pytest.mark.parametrize(
    "cbr",
    [
        (("cname",), ("cname", 5, 30, [])),
        (("cname", 7), ("cname", 7, 30, [])),
        (("cname", 7, 42), ("cname", 7, 42, [])),
        (("cname", 7, 42, [ValueError]), ("cname", 7, 42, [ValueError])),
    ],
)
@pytest.mark.asyncio
async def test_circuitbreaker_factory_get_breaker(
    uow,
    cbr,
    circuitbreaker: CircuitBreakerFactory,
    circuitbreaker_redis: CircuitBreakerFactory,
):
    cbreaker = {"inmemory": circuitbreaker, "redis": circuitbreaker_redis}[uow]
    await cbreaker.initialize()

    breaker = await cbreaker.get_breaker(*cbr[0])
    assert breaker.context.name == cbr[1][0]
    assert breaker.context.threshold == cbr[1][1]
    assert breaker.context.ttl == cbr[1][2]
    assert breaker.context.exclude_list == cbr[1][3]


@pytest.mark.parametrize("state", ["closed", "opened", "half-opened"])
def test_circuitbreaker_repr(state):
    circuitbreaker = Context("plop", 5, 30, state)
    assert (
        repr(circuitbreaker)
        == f'<Context name="plop" state="{state}" threshold="5" ttl="30">'
    )


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
    assert cast(InMemoryRepository, circuitbreaker.uow.circuit_breakers).breakers == {
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


@pytest.mark.asyncio
async def test_circuitbreaker_raise_state_changed_event(circuitbreaker):

    evts = []

    async def evt_handler(cmd: ContextChanged, uow):
        evts.append(asdict(cmd))

    circuitbreaker.messagebus.add_listener(ContextChanged, evt_handler)
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
            "state": "opened",
        },
    ]


@pytest.mark.asyncio
async def test_circuit_breaker_factory_global_exclude():
    circuitbreaker = CircuitBreakerFactory(exclude=[ValueError])

    @circuitbreaker("my", threshold=1, exclude=[KeyError])
    async def raise_error(typ_: str):
        if typ_ == "value":
            raise ValueError(42)
        if typ_ == "key":
            raise KeyError(42)
        raise RuntimeError("boom")

    try:
        await raise_error("value")
    except ValueError:
        pass

    assert (await circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (await circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        await raise_error("key")
    except KeyError:
        pass

    assert (await circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (await circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        await raise_error("runtime")
    except RuntimeError:
        pass

    assert (await circuitbreaker.get_breaker("my")).context.state == "opened"


@pytest.mark.asyncio
async def test_circuitbreaker_factory_add_listener():

    evts = []

    def hook(name, evt_name, evt):
        evts.append((name, evt_name, evt))

    circuitbreaker = CircuitBreakerFactory(default_threshold=2, default_ttl=0.1)
    circuitbreaker.add_listener(hook)

    brk = await circuitbreaker.get_breaker("my")
    brk2 = await circuitbreaker.get_breaker("my2")

    async def boom():
        try:
            async with brk:
                raise RuntimeError("Boom")
        except RuntimeError:
            pass

    await boom()
    async with brk2:
        pass

    await boom()

    assert evts == [
        (
            "my",
            "circuit_breaker_created",
            CircuitBreakerCreated(name="my", threshold=2, ttl=0.1),
        ),
        (
            "my2",
            "circuit_breaker_created",
            CircuitBreakerCreated(name="my2", threshold=2, ttl=0.1),
        ),
        ("my", "failed", CircuitBreakerFailed(name="my", failure_count=1)),
        (
            "my",
            "state_changed",
            ContextChanged(
                name="my", state="opened", opened_at=brk.context._state.opened_at
            ),
        ),
    ]

    evts.clear()
    await asyncio.sleep(0.11)
    await boom()
    assert evts == [
        (
            "my",
            "state_changed",
            ContextChanged(name="my", state="half-opened", opened_at=None),
        ),
        (
            "my",
            "state_changed",
            ContextChanged(
                name="my", state="opened", opened_at=brk.context._state.opened_at
            ),
        ),
    ]
    evts.clear()

    await asyncio.sleep(0.11)
    async with brk:
        pass

    assert evts == [
        (
            "my",
            "state_changed",
            ContextChanged(name="my", state="half-opened", opened_at=None),
        ),
        ("my", "recovered", CircuitBreakerRecovered(name="my")),
        (
            "my",
            "state_changed",
            ContextChanged(name="my", state="closed", opened_at=None),
        ),
    ]


@pytest.mark.asyncio
async def test_circuitbreaker_factory_remove_listener():

    evts = []

    class Hook:
        def __call__(self, name, evt_name, evt):
            evts.append((name, evt_name, evt))

        def __repr__(self):
            return "<hook>"

    hook = Hook()
    hook2 = Hook()

    circuitbreaker = CircuitBreakerFactory(default_threshold=2, default_ttl=0.1)
    with pytest.raises(RuntimeError) as ctx:
        circuitbreaker.remove_listener(hook)
    assert str(ctx.value) == f"<hook> is not listening {circuitbreaker}"

    circuitbreaker.add_listener(hook)
    await circuitbreaker.get_breaker("my")
    assert evts == [
        (
            "my",
            "circuit_breaker_created",
            CircuitBreakerCreated(name="my", threshold=2, ttl=0.1),
        ),
    ]
    evts.clear()
    circuitbreaker.add_listener(hook2)
    assert len(circuitbreaker.listeners) == 2
    circuitbreaker.remove_listener(hook)
    assert len(circuitbreaker.listeners) == 1
    circuitbreaker.remove_listener(hook2)
    await circuitbreaker.get_breaker("my2")
    assert evts == []
    assert circuitbreaker.listeners == {}
