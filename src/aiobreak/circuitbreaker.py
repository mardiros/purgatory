import asyncio
from dataclasses import dataclass
from functools import wraps
from types import TracebackType
from typing import Any, Callable, Optional, Type, cast

from aiobreak.domain.model import Context


class CircuitBreaker:
    name: str

    def __init__(self, name: str, threshold: int, ttl: float):
        self.name = name
        self._state = Context(threshold, ttl)

    async def __aenter__(self) -> "CircuitBreaker":
        await self._state.handle_new_request()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if exc:
            return await self._state.handle_exception(exc)
        else:
            return await self._state.handle_end_request()

    def __repr__(self) -> str:
        return f'<CircuitBreaker name="{self.name}" threshold="{self._state.threshold}" ttl="{self._state.ttl}">'

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, CircuitBreaker)
            and self.name == other.name
            and self._state == other._state
        )


class CircuitBreakerFactory:
    def __init__(self, default_threshold: int = 5, default_ttl: int = 300):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.breakers = {}

    def get_breaker(
        self, circuit: str, threshold: Optional[int] = None, ttl: Optional[int] = None
    ) -> CircuitBreaker:
        if circuit not in self.breakers:
            self.breakers[circuit] = CircuitBreaker(
                circuit, threshold or self.default_threshold, ttl or self.default_ttl
            )
        return self.breakers[circuit]

    def __call__(self, circuit: str, threshold=None, ttl=None) -> Any:

        circuit_breaker = self.get_breaker(circuit, threshold, ttl)

        @wraps
        def decorator(self, func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                async with circuit_breaker:
                    return await func(*args, **kwds)

            return inner_coro

        return decorator
