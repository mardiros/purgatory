from functools import wraps
from typing import Any, Callable, Optional

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.messages.commands import (
    CreateCircuitBreaker,
)
from purgatory.domain.messages.events import CircuitBreakerStateChanged
from purgatory.service.handlers import register_circuit_breaker
from purgatory.service.handlers.circuitbreaker import save_circuit_breaker_state
from purgatory.service.messagebus import MessageRegistry
from purgatory.service.unit_of_work import AbstractUnitOfWork, InMemoryUnitOfWork


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

    async def get_breaker(
        self, circuit: str, threshold=None, ttl=None
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
        return brk

    def __call__(self, circuit: str, threshold=None, ttl=None) -> Any:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                brk = await self.get_breaker(circuit, threshold, ttl)
                try:
                    with brk:
                        return await func(*args, **kwds)
                finally:
                    if brk._dirty:
                        await self.messagebus.handle(
                            CircuitBreakerStateChanged(
                                brk.name,
                                brk.state,
                                brk.opened_at,
                                brk.failure_count,
                            ),
                            self.uow,
                        )

            return inner_coro

        return decorator
