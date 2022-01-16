from functools import wraps
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Type

from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context, ExcludeType
from purgatory.service._sync.message_handlers import (
    inc_circuit_breaker_failure,
    register_circuit_breaker,
    reset_failure,
    save_circuit_breaker_state,
)
from purgatory.service._sync.messagebus import SyncMessageRegistry
from purgatory.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncInMemoryUnitOfWork,
)
from purgatory.typing import TTL, CircuitName, Hook, Threshold


class SyncCircuitBreaker:
    def __init__(
        self,
        context: Context,
        uow: SyncAbstractUnitOfWork,
        messagebus: SyncMessageRegistry,
    ) -> None:
        self.context = context
        self.uow = uow
        self.messagebus = messagebus

    def __enter__(self) -> "SyncCircuitBreaker":
        self.context.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.context.__exit__(exc_type, exc, tb)
        while self.context.messages:
            self.messagebus.handle(
                self.context.messages.pop(0),
                self.uow,
            )


class PublicEvent:
    def __init__(self, messagebus: SyncMessageRegistry, hook: Hook) -> None:
        messagebus.add_listener(CircuitBreakerCreated, self.cb_created)
        messagebus.add_listener(ContextChanged, self.cb_state_changed)
        messagebus.add_listener(CircuitBreakerFailed, self.cb_failed)
        messagebus.add_listener(CircuitBreakerRecovered, self.cb_recovered)
        self.hook = hook

    def remove_listeners(self, messagebus: SyncMessageRegistry) -> None:
        messagebus.remove_listener(CircuitBreakerCreated, self.cb_created)
        messagebus.remove_listener(ContextChanged, self.cb_state_changed)
        messagebus.remove_listener(CircuitBreakerFailed, self.cb_failed)
        messagebus.remove_listener(CircuitBreakerRecovered, self.cb_recovered)

    def cb_created(
        self, event: CircuitBreakerCreated, uow: SyncAbstractUnitOfWork
    ) -> None:
        self.hook(event.name, "circuit_breaker_created", event)

    def cb_state_changed(
        self, event: CircuitBreakerCreated, uow: SyncAbstractUnitOfWork
    ) -> None:
        self.hook(event.name, "state_changed", event)

    def cb_failed(
        self, event: CircuitBreakerCreated, uow: SyncAbstractUnitOfWork
    ) -> None:
        self.hook(event.name, "failed", event)

    def cb_recovered(
        self, event: CircuitBreakerCreated, uow: SyncAbstractUnitOfWork
    ) -> None:
        self.hook(event.name, "recovered", event)


class SyncCircuitBreakerFactory:
    def __init__(
        self,
        default_threshold: Threshold = 5,
        default_ttl: TTL = 30,
        exclude: ExcludeType = None,
        uow: Optional[SyncAbstractUnitOfWork] = None,
    ):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.global_exclude = exclude or []
        self.uow = uow or SyncInMemoryUnitOfWork()
        self.messagebus = SyncMessageRegistry()
        self.messagebus.add_listener(CreateCircuitBreaker, register_circuit_breaker)
        self.messagebus.add_listener(ContextChanged, save_circuit_breaker_state)
        self.messagebus.add_listener(CircuitBreakerFailed, inc_circuit_breaker_failure)
        self.messagebus.add_listener(CircuitBreakerRecovered, reset_failure)
        self.listeners: Dict[Hook, PublicEvent] = {}

    def initialize(self) -> None:
        self.uow.initialize()

    def add_listener(self, listener: Hook) -> None:
        self.listeners[listener] = PublicEvent(self.messagebus, listener)

    def remove_listener(self, listener: Hook) -> None:
        try:
            self.listeners[listener].remove_listeners(self.messagebus)
            del self.listeners[listener]
        except KeyError:
            raise RuntimeError(f"{listener} is not listening {self}")

    def get_breaker(
        self,
        circuit: CircuitName,
        threshold: Optional[Threshold] = None,
        ttl: Optional[TTL] = None,
        exclude: ExcludeType = None,
    ) -> SyncCircuitBreaker:
        with self.uow as uow:
            brk = uow.contexts.get(circuit)
        if brk is None:
            with self.uow as uow:
                bkr_threshold = threshold or self.default_threshold
                bkr_ttl = ttl or self.default_ttl
                brk = self.messagebus.handle(
                    CreateCircuitBreaker(circuit, bkr_threshold, bkr_ttl),
                    self.uow,
                )
        brk.exclude_list = (exclude or []) + self.global_exclude
        return SyncCircuitBreaker(brk, self.uow, self.messagebus)

    def __call__(
        self,
        circuit: str,
        threshold: Optional[Threshold] = None,
        ttl: Optional[TTL] = None,
        exclude: ExcludeType = None,
    ) -> Any:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def inner_coro(*args: Any, **kwargs: Any) -> Any:
                brk = self.get_breaker(circuit, threshold, ttl, exclude)
                with brk:
                    return func(*args, **kwargs)

            return inner_coro

        return decorator
