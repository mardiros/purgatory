from typing import Any

try:
    from aioredis import Redis as AioRedis

    AsyncRedis = AioRedis
except ImportError:
    AsyncRedis = Any  # type: ignore

try:
    from redis import Redis

    SyncRedis = Redis
except ImportError:
    SyncRedis = Any  # type: ignore
