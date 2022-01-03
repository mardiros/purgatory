import time

import pytest

from purgatory.domain.model import Context
from purgatory.service._async.repository import (
    AsyncInMemoryRepository,
    AsyncRedisRepository,
)


@pytest.mark.parametrize("repository", ["inmemory", "redis"])
@pytest.mark.parametrize("state", ["half-opened", "opened", "closed"])
@pytest.mark.asyncio
async def test_redis_respository_state_recovery(
    state,
    repository,
    inmemory_repository: AsyncInMemoryRepository,
    redis_repository: AsyncRedisRepository,
):
    repository = {"inmemory": inmemory_repository, "redis": redis_repository}[
        repository
    ]
    context = Context("foo", 40, 10, state)
    await repository.initialize()
    await repository.register(context)
    context2 = await repository.get("foo")
    assert context2 == context


@pytest.mark.parametrize("repository", ["redis"])
@pytest.mark.asyncio
async def test_redis_respository_workflow(
    repository,
    # the in memory repository works update its state in the model,
    # and does not affect the repository
    # inmemory_repository: AsyncInMemoryRepository,
    redis_repository: AsyncRedisRepository,
):
    repository = {"redis": redis_repository}[repository]

    breaker = Context("foo", 40, 10)
    await repository.initialize()
    await repository.register(breaker)

    await repository.inc_failures("foo", 1)
    breaker = await repository.get("foo")
    assert breaker.failure_count == 1

    await repository.inc_failures("foo", 2)
    breaker = await repository.get("foo")
    assert breaker.failure_count == 2

    opened_at = time.time()
    await repository.update_state("foo", state="opened", opened_at=opened_at)
    breaker = await repository.get("foo")
    assert breaker.failure_count == 2
    assert breaker.opened_at == opened_at

    await repository.update_state("foo", state="half-opened", opened_at=None)
    breaker = await repository.get("foo")
    assert breaker.opened_at is None

    await repository.reset_failure("foo")
    breaker = await repository.get("foo")
    assert breaker.failure_count == 0

    await repository.update_state("foo", state="closed", opened_at=None)
    breaker = await repository.get("foo")
    assert breaker.opened_at is None
