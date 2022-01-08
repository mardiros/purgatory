from dataclasses import asdict

import pytest

from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context
from purgatory.service._sync.circuitbreaker import SyncCircuitBreakerFactory
from tests.unittests.time import SyncSleep


@pytest.mark.asyncio
def test_circuitbreaker_factory_decorator(
    circuitbreaker: SyncCircuitBreakerFactory,
):

    count = 0

    @circuitbreaker(circuit="client")
    def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1

    fail_or_success()
    assert count == 1

    with pytest.raises(RuntimeError):
        fail_or_success(fail=True)

    brk = circuitbreaker.uow.contexts.get("client")
    assert brk == Context(name="client", threshold=5, ttl=30)
    # assert circuitbreaker.breakers["client"]._state._state.failure_count == 1

    @circuitbreaker(circuit="client2", threshold=15)
    def _success2():
        pass

    _success2()
    brk = circuitbreaker.uow.contexts.get("client2")
    assert brk == Context(name="client2", threshold=15, ttl=30)

    @circuitbreaker(circuit="client3", ttl=60)
    def _success3():
        pass

    _success3()
    brk = circuitbreaker.uow.contexts.get("client3")
    assert brk == Context(name="client3", threshold=5, ttl=60)


@pytest.mark.asyncio
def test_redis_circuitbreaker_factory_decorator(
    fake_redis, circuitbreaker_redis: SyncCircuitBreakerFactory
):

    count = 0
    circuitbreaker_redis.initialize()

    @circuitbreaker_redis(circuit="client", threshold=3, ttl=0.1)
    def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1

    def fail():
        try:
            fail_or_success(True)
        except RuntimeError:
            pass

    fail()
    fail()

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

    fail_or_success(fail=False)
    fail()


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
def test_circuitbreaker_factory_get_breaker(
    uow,
    cbr,
    circuitbreaker: SyncCircuitBreakerFactory,
    circuitbreaker_redis: SyncCircuitBreakerFactory,
):
    cbreaker = {"inmemory": circuitbreaker, "redis": circuitbreaker_redis}[uow]
    cbreaker.initialize()

    breaker = cbreaker.get_breaker(*cbr[0])
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
def test_circuitbreaker_raise_state_changed_event(circuitbreaker):

    evts = []

    def evt_handler(cmd: ContextChanged, uow):
        evts.append(asdict(cmd))

    circuitbreaker.messagebus.add_listener(ContextChanged, evt_handler)
    brk = circuitbreaker.get_breaker("my", threshold=2)
    try:
        with brk:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert evts == []

    try:
        with brk:
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
def test_circuit_breaker_factory_global_exclude():
    circuitbreaker = SyncCircuitBreakerFactory(exclude=[ValueError])

    @circuitbreaker("my", threshold=1, exclude=[KeyError])
    def raise_error(typ_: str):
        if typ_ == "value":
            raise ValueError(42)
        if typ_ == "key":
            raise KeyError(42)
        raise RuntimeError("boom")

    try:
        raise_error("value")
    except ValueError:
        pass

    assert (circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        raise_error("key")
    except KeyError:
        pass

    assert (circuitbreaker.get_breaker("my")).context.state == "closed"
    assert (circuitbreaker.get_breaker("my")).context._state.failure_count == 0

    try:
        raise_error("runtime")
    except RuntimeError:
        pass

    assert (circuitbreaker.get_breaker("my")).context.state == "opened"


@pytest.mark.asyncio
def test_circuitbreaker_factory_add_listener():

    evts = []

    def hook(name, evt_name, evt):
        evts.append((name, evt_name, evt))

    circuitbreaker = SyncCircuitBreakerFactory(default_threshold=2, default_ttl=0.1)
    circuitbreaker.add_listener(hook)

    brk = circuitbreaker.get_breaker("my")
    brk2 = circuitbreaker.get_breaker("my2")

    def boom():
        try:
            with brk:
                raise RuntimeError("Boom")
        except RuntimeError:
            pass

    boom()
    with brk2:
        pass

    boom()

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
        ("my", "failed", CircuitBreakerFailed(name="my", failure_count=2)),
        (
            "my",
            "state_changed",
            ContextChanged(
                name="my", state="opened", opened_at=brk.context._state.opened_at
            ),
        ),
    ]

    evts.clear()
    SyncSleep(0.11)
    boom()
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

    SyncSleep(0.11)
    with brk:
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
def test_circuitbreaker_factory_remove_listener():

    evts = []

    class Hook:
        def __call__(self, name, evt_name, evt):
            evts.append((name, evt_name, evt))

        def __repr__(self):
            return "<hook>"

    hook = Hook()
    hook2 = Hook()

    circuitbreaker = SyncCircuitBreakerFactory(default_threshold=2, default_ttl=0.1)
    with pytest.raises(RuntimeError) as ctx:
        circuitbreaker.remove_listener(hook)
    assert str(ctx.value) == f"<hook> is not listening {circuitbreaker}"

    circuitbreaker.add_listener(hook)
    circuitbreaker.get_breaker("my")
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
    circuitbreaker.get_breaker("my2")
    assert evts == []
    assert circuitbreaker.listeners == {}
