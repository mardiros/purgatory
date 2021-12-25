from functools import wraps
from typing import Any, Callable, Dict, Optional

from aiobreak.domain.model import CircuitBreaker


class CircuitBreakerFactory:
    def __init__(self, default_threshold: int = 5, default_ttl: int = 300):
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.breakers: Dict[str, CircuitBreaker] = {}

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

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                async with circuit_breaker:
                    return await func(*args, **kwds)

            return inner_coro

        return decorator
