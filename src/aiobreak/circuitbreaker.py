import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, cast


@dataclass
class CircuitBreaker:
    name: str
    threshold: int

    def __enter__(self) -> "CircuitBreaker":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    async def __aenter__(self) -> "CircuitBreaker":
        return self.__enter__()

    async def __aexit__(self, *exc: Any) -> None:
        return self.__exit__(*exc)


class CircuitBreakerFactory:
    def __init__(self, default_threshold=5):
        self.default_threshold = default_threshold
        self.breakers = {}

    def get_breaker(self, circuit: str, threshold=None) -> CircuitBreaker:
        if circuit not in self.breakers:
            self.breakers[circuit] = CircuitBreaker(
                circuit, threshold or self.default_threshold
            )
        return self.breakers[circuit]

    def __call__(self, circuit: str, threshold=None) -> Any:

        circuit_breaker = self.get_breaker(circuit, threshold)

        @wraps
        def decorator(self, func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                async with circuit_breaker:
                    return await func(*args, **kwds)

            return inner_coro

        return decorator
