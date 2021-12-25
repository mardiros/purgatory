from functools import wraps
from typing import Any, Callable, Optional
from purgatory.domain.messages.commands import CreateCircuitBreaker

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.service import messagebus
from purgatory.service.unit_of_work import AbstractUnitOfWork, InMemoryUnitOfWork
from purgatory.service.handlers import register_circuit_breaker

messagebus.add_listener(CreateCircuitBreaker, register_circuit_breaker)


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

    async def get_breaker(self, circuit: str, threshold=None, ttl=None):
        async with self.uow as uow:
            brk = await uow.circuit_breakers.get(circuit)
        if brk is None:
            async with self.uow as uow:
                bkr_threshold = threshold or self.default_threshold
                bkr_ttl = ttl or self.default_ttl
                await messagebus.handle(
                    CreateCircuitBreaker(circuit, bkr_threshold, bkr_ttl),
                    self.uow,
                )
                brk = CircuitBreaker(circuit, bkr_threshold, bkr_ttl)
        return brk

    def __call__(self, circuit: str, threshold=None, ttl=None) -> Any:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                brk = await self.get_breaker(circuit, threshold, ttl)
                async with brk:
                    return await func(*args, **kwds)

            return inner_coro

        return decorator
