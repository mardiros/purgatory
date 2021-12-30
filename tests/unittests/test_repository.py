import pytest

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.repository import InMemoryRepository, RedisRepository


@pytest.mark.parametrize("repository", ["inmemory", "redis"])
@pytest.mark.parametrize("state", ["half-opened", "opened", "closed"])
@pytest.mark.asyncio
async def test_redis_respository_state_recovery(
    state,
    repository,
    inmemory_repository: InMemoryRepository,
    redis_repository: RedisRepository,
):
    repository = {"inmemory": inmemory_repository, "redis": redis_repository}[
        repository
    ]
    breaker = CircuitBreaker("foo", 40, 10, state)
    await repository.initialize()
    await repository.register(breaker)
    breaker2 = await repository.get("foo")
    assert breaker2 == breaker


@pytest.mark.parametrize("repository", ["redis"])
@pytest.mark.asyncio
async def test_redis_respository_workflow(
    repository,
    # the in memory repository works update its state in the model,
    # and does not affect the repository
    # inmemory_repository: InMemoryRepository,
    redis_repository: RedisRepository,
):
    repository = {"redis": redis_repository}[
        repository
    ]

    breaker = CircuitBreaker("foo", 40, 10)
    await repository.initialize()
    await repository.register(breaker)

    await repository.inc_failures("foo", 1)
    breaker = await repository.get("foo")
    assert breaker.failure_count == 1

    await repository.inc_failures("foo", 2)
    breaker = await repository.get("foo")
    assert breaker.failure_count == 2

    await repository.reset_failure("foo")
    breaker = await repository.get("foo")
    assert breaker.failure_count == 0
