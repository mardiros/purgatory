import asyncio
from functools import wraps
from typing import Any, Callable, cast


class CircuitBreaker:

    def __init__(self):
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:

        @wraps
        def decorator(self, func: Callable) -> Callable:

            if asyncio.iscoroutinefunction(cast(Any, func)):
                @wraps(func)
                async def inner_coro(*args: Any, **kwds: Any) -> Any:
                    async with self:
                        return await func(*args, **kwds)

                return inner_coro
            else:

                @wraps(func)
                def inner(*args: Any, **kwds: Any) -> Any:
                    with self:
                        return func(*args, **kwds)

                return inner
        return decorator

    def __enter__(self) -> "CircuitBreaker":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    async def __aenter__(self) -> "CircuitBreaker":
        return self.__enter__()

    async def __aexit__(self, *exc: Any) -> None:
        return self.__exit__(*exc)
