import pytest

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.repository import InMemoryRepository, RedisRepository


@pytest.mark.asyncio
async def test_timeslot_in_memory_repository():
    repo = InMemoryRepository()
    cbreaker = CircuitBreaker("dummy", 5, 30.0)
    await repo.register(cbreaker)
    assert repo.breakers == {"dummy": cbreaker}


@pytest.mark.parametrize("state", ["half-opened", "opened", "closed"])
@pytest.mark.asyncio
async def test_redis_respository(state, redis_repository: RedisRepository):
    breaker = CircuitBreaker("foo", 40, 10, state)
    await redis_repository.initialize()
    await redis_repository.register(breaker)
    breaker2 = await redis_repository.get("foo")
    assert breaker2 == breaker
