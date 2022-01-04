import json
from typing import Any, Optional, cast

import pytest

from purgatory import SyncCircuitBreakerFactory
from purgatory.service._sync.messagebus import SyncMessageRegistry
from purgatory.service._sync.repository import (
    SyncInMemoryRepository,
    SyncRedisRepository,
)
from purgatory.service._sync.unit_of_work import SyncRedisUnitOfWork


@pytest.fixture()
def circuitbreaker():
    yield SyncCircuitBreakerFactory()


@pytest.fixture()
def messagebus():
    yield SyncMessageRegistry()


class FakeRedis:
    def __init__(self):
        self.initialized = False
        self.storage = None

    @property
    def deserialized_storage(self):
        return {
            key: json.loads(val) if isinstance(val, str) else val
            for key, val in self.storage.items()
        }

    def initialize(self):
        self.initialized = True
        self.storage = {}

    def get(self, key) -> Optional[Any]:
        if not self.initialized:
            raise RuntimeError("Unititialized")
        return self.storage.get(key)

    def set(self, key, val):
        if not self.initialized:
            raise RuntimeError("Unititialized")
        self.storage[key] = val

    def incr(self, key):
        if not self.initialized:
            raise RuntimeError("Unititialized")
        val = int(self.storage.get(key, 0)) + 1
        self.storage[key] = val


@pytest.fixture()
def fake_redis():
    yield FakeRedis()


@pytest.fixture()
def inmemory_repository():
    return SyncInMemoryRepository()


@pytest.fixture()
def redis_repository(fake_redis):
    repo = SyncRedisRepository("redis://localhost")
    repo.redis = fake_redis
    yield repo


@pytest.fixture()
def redis_uow(fake_redis):
    repo = SyncRedisUnitOfWork("redis://localhost")
    cast(SyncRedisRepository, repo.contexts).redis = fake_redis
    yield repo


@pytest.fixture()
def circuitbreaker_redis(redis_uow):
    yield SyncCircuitBreakerFactory(uow=redis_uow)
