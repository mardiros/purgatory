from functools import wraps
from types import TracebackType
from typing import Any, Callable, Optional, Type

from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerStateChanged,
)
from purgatory.domain.model import CircuitBreaker
from purgatory.service.handlers import register_circuit_breaker
from purgatory.service.handlers.circuitbreaker import (
    inc_circuit_breaker_failure,
    save_circuit_breaker_state,
)
from purgatory.service.messagebus import MessageRegistry
from purgatory.service.unit_of_work import AbstractUnitOfWork, InMemoryUnitOfWork


class CircuitBreakerService:
    def __init__(
        self, brk: CircuitBreaker, uow: AbstractUnitOfWork, messagebus: MessageRegistry
    ) -> None:
        self.brk = brk
        self.uow = uow
        self.messagebus = messagebus

    async def __aenter__(self) -> "CircuitBreakerService":
        self.brk.__enter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.brk.__exit__(exc_type, exc, tb)
        while self.brk.messages:
            await self.messagebus.handle(
                self.brk.messages.pop(0),
                self.uow,
            )


class CircuitBreakerFactory:
    def __init__(
        self,
        default_threshold: int = 5,
        default_ttl: int = 300,
        uow: Optional[AbstractUnitOfWork] = None,
    ):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.uow = uow or InMemoryUnitOfWork()
        self.messagebus = MessageRegistry()
        self.messagebus.add_listener(CreateCircuitBreaker, register_circuit_breaker)
        self.messagebus.add_listener(
            CircuitBreakerStateChanged, save_circuit_breaker_state
        )
        self.messagebus.add_listener(CircuitBreakerFailed, inc_circuit_breaker_failure)

    async def initialize(self):
        await self.uow.initialize()

    async def get_breaker(
        self, circuit: str, threshold=None, ttl=None
    ) -> CircuitBreakerService:
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
        return CircuitBreakerService(brk, self.uow, self.messagebus)

    def __call__(self, circuit: str, threshold=None, ttl=None) -> Any:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                brk = await self.get_breaker(circuit, threshold, ttl)
                async with brk:
                    return await func(*args, **kwds)

            return inner_coro

        return decorator
