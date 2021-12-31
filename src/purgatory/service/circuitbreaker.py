from functools import wraps
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Type

from purgatory.domain.messages.base import Event
from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context, ExcludeType
from purgatory.service.handlers import register_circuit_breaker
from purgatory.service.handlers.circuitbreaker import (
    inc_circuit_breaker_failure,
    reset_failure,
    save_circuit_breaker_state,
)
from purgatory.service.messagebus import MessageRegistry
from purgatory.service.unit_of_work import AbstractUnitOfWork, InMemoryUnitOfWork


class CircuitBreaker:
    def __init__(
        self, context: Context, uow: AbstractUnitOfWork, messagebus: MessageRegistry
    ) -> None:
        self.context = context
        self.uow = uow
        self.messagebus = messagebus

    async def __aenter__(self) -> "CircuitBreaker":
        self.context.__enter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.context.__exit__(exc_type, exc, tb)
        while self.context.messages:
            await self.messagebus.handle(
                self.context.messages.pop(0),
                self.uow,
            )


class PublicEvent:
    def __init__(
        self, messagebus: MessageRegistry, hook: Callable[[str, str, Event], None]
    ) -> None:
        messagebus.add_listener(CircuitBreakerCreated, self.cb_created)
        messagebus.add_listener(ContextChanged, self.cb_state_changed)
        messagebus.add_listener(CircuitBreakerFailed, self.cb_failed)
        messagebus.add_listener(CircuitBreakerRecovered, self.cb_recovered)
        self.hook = hook

    def remove_listeners(self, messagebus: MessageRegistry) -> None:
        messagebus.remove_listener(CircuitBreakerCreated, self.cb_created)
        messagebus.remove_listener(ContextChanged, self.cb_state_changed)
        messagebus.remove_listener(CircuitBreakerFailed, self.cb_failed)
        messagebus.remove_listener(CircuitBreakerRecovered, self.cb_recovered)

    async def cb_created(self, event: CircuitBreakerCreated, uow: AbstractUnitOfWork):
        self.hook(event.name, "circuit_breaker_created", event)

    async def cb_state_changed(
        self, event: CircuitBreakerCreated, uow: AbstractUnitOfWork
    ):
        self.hook(event.name, "state_changed", event)

    async def cb_failed(self, event: CircuitBreakerCreated, uow: AbstractUnitOfWork):
        self.hook(event.name, "failed", event)

    async def cb_recovered(self, event: CircuitBreakerCreated, uow: AbstractUnitOfWork):
        self.hook(event.name, "recovered", event)


class CircuitBreakerFactory:
    def __init__(
        self,
        default_threshold: int = 5,
        default_ttl: float = 30,
        exclude: ExcludeType = None,
        uow: Optional[AbstractUnitOfWork] = None,
    ):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.global_exclude = exclude or []
        self.uow = uow or InMemoryUnitOfWork()
        self.messagebus = MessageRegistry()
        self.messagebus.add_listener(CreateCircuitBreaker, register_circuit_breaker)
        self.messagebus.add_listener(
            ContextChanged, save_circuit_breaker_state
        )
        self.messagebus.add_listener(CircuitBreakerFailed, inc_circuit_breaker_failure)
        self.messagebus.add_listener(CircuitBreakerRecovered, reset_failure)
        self.listeners: Dict[Callable, Any] = {}

    async def initialize(self):
        await self.uow.initialize()

    def add_listener(self, listener):
        self.listeners[listener] = PublicEvent(self.messagebus, listener)

    def remove_listener(self, listener):
        try:
            self.listeners[listener].remove_listeners(self.messagebus)
            del self.listeners[listener]
        except KeyError:
            raise RuntimeError(f"{listener} is not listening {self}")

    async def get_breaker(
        self, circuit: str, threshold=None, ttl=None, exclude: ExcludeType = None
    ) -> CircuitBreaker:
        async with self.uow as uow:
            brk = await uow.circuit_breakers.get(circuit)
        if brk is None:
            async with self.uow as uow:
                bkr_threshold = threshold or self.default_threshold
                bkr_ttl = ttl or self.default_ttl
                brk = await self.messagebus.handle(
                    CreateCircuitBreaker(circuit, bkr_threshold, bkr_ttl),
                    self.uow,
                )
        brk.exclude_list = (exclude or []) + self.global_exclude
        return CircuitBreaker(brk, self.uow, self.messagebus)

    def __call__(
        self, circuit: str, threshold=None, ttl=None, exclude: ExcludeType = None
    ) -> Any:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwargs: Any) -> Any:
                brk = await self.get_breaker(circuit, threshold, ttl, exclude)
                async with brk:
                    return await func(*args, **kwargs)

            return inner_coro

        return decorator
