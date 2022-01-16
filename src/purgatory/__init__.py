import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("purgatory-circuitbreaker").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass


from purgatory.domain.messages import Event
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.service._async.circuitbreaker import AsyncCircuitBreakerFactory
from purgatory.service._async.unit_of_work import (
    AsyncAbstractUnitOfWork,
    AsyncInMemoryUnitOfWork,
    AsyncRedisUnitOfWork,
)
from purgatory.service._sync.circuitbreaker import SyncCircuitBreakerFactory
from purgatory.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncInMemoryUnitOfWork,
    SyncRedisUnitOfWork,
)

__all__ = [
    "AsyncAbstractUnitOfWork",
    "AsyncCircuitBreakerFactory",
    "AsyncInMemoryUnitOfWork",
    "AsyncRedisUnitOfWork",
    "CircuitBreakerCreated",
    "CircuitBreakerFailed",
    "CircuitBreakerRecovered",
    "ContextChanged",
    "Event",
    "SyncCircuitBreakerFactory",
    "SyncAbstractUnitOfWork",
    "SyncInMemoryUnitOfWork",
    "SyncRedisUnitOfWork",
]
