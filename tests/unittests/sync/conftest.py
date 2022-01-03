import json
from typing import Any, Optional, cast

import pytest

from purgatory.sync import SyncCircuitBreakerFactory
from purgatory.sync.messagebus import SyncMessageRegistry
from purgatory.sync.repository import SyncInMemoryRepository, SyncRedisRepository
from purgatory.sync.unit_of_work import SyncRedisUnitOfWork


@pytest.fixture()
def sync_circuitbreaker():
    yield SyncCircuitBreakerFactory()


@pytest.fixture()
def messagebus():
    yield SyncMessageRegistry()


class FakeSyncRedis:
    def __init__(self):
        self.initialized = True
        self.storage = {}

    @property
    def deserialized_storage(self):
        return {
            key: json.loads(val) if isinstance(val, str) else val
            for key, val in self.storage.items()
        }

    def initialize(self):
        pass

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
def sync_fake_redis():
    yield FakeSyncRedis()


@pytest.fixture()
def sync_inmemory_repository():
    return SyncInMemoryRepository()


@pytest.fixture()
def sync_redis_repository(sync_fake_redis):
    repo = SyncRedisRepository("redis://localhost")
    repo.redis = sync_fake_redis
    yield repo


@pytest.fixture()
def sync_redis_uow(sync_fake_redis):
    repo = SyncRedisUnitOfWork("redis://localhost")
    cast(SyncRedisRepository, repo.contexts).redis = sync_fake_redis
    yield repo


@pytest.fixture()
def sync_circuitbreaker_redis(sync_redis_uow):
    yield SyncCircuitBreakerFactory(uow=sync_redis_uow)
