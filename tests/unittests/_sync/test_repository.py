import time

import pytest

from purgatory.domain.model import Context
from purgatory.service._sync.repository import (
    SyncInMemoryRepository,
    SyncRedisRepository,
)


@pytest.mark.parametrize("repository", ["inmemory", "redis"])
@pytest.mark.parametrize("state", ["half-opened", "opened", "closed"])
def test_redis_respository_state_recovery(
    state,
    repository,
    inmemory_repository: SyncInMemoryRepository,
    redis_repository: SyncRedisRepository,
):
    repository = {"inmemory": inmemory_repository, "redis": redis_repository}[
        repository
    ]
    context = Context("foo", 40, 10, state)
    repository.initialize()
    repository.register(context)
    context2 = repository.get("foo")
    assert context2 == context


@pytest.mark.parametrize("repository", ["redis"])
def test_redis_respository_workflow(
    repository,
    # the in memory repository works update its state in the model,
    # and does not affect the repository
    # inmemory_repository: AsyncInMemoryRepository,
    redis_repository: SyncRedisRepository,
):
    repository = {"redis": redis_repository}[repository]

    breaker = Context("foo", 40, 10)
    repository.initialize()
    repository.register(breaker)

    repository.inc_failures("foo", 1)
    breaker = repository.get("foo")
    assert breaker.failure_count == 1

    repository.inc_failures("foo", 2)
    breaker = repository.get("foo")
    assert breaker.failure_count == 2

    opened_at = time.time()
    repository.update_state("foo", state="opened", opened_at=opened_at)
    breaker = repository.get("foo")
    assert breaker.failure_count == 2
    assert breaker.opened_at == opened_at

    repository.update_state("foo", state="half-opened", opened_at=None)
    breaker = repository.get("foo")
    assert breaker.opened_at is None

    repository.reset_failure("foo")
    breaker = repository.get("foo")
    assert breaker.failure_count == 0

    repository.update_state("foo", state="closed", opened_at=None)
    breaker = repository.get("foo")
    assert breaker.opened_at is None
