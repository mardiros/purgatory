import requests

from purgatory import SyncCircuitBreakerFactory, SyncRedisUnitOfWork

circuit_breaker = SyncCircuitBreakerFactory(
    default_threshold=5,
    default_ttl=30,
    exclude=[
        (requests.HTTPError, lambda exc: 400 <= exc.response.status_code < 500),
    ],
    uow=SyncRedisUnitOfWork("redis://localhost/0"),
)
