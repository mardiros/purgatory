import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("purgatory").version
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
from purgatory.service.circuitbreaker import CircuitBreakerFactory
from purgatory.service.unit_of_work import (
    AbstractUnitOfWork,
    InMemoryUnitOfWork,
    RedisUnitOfWork,
)

__all__ = [
    "CircuitBreakerFactory",
    "Event",
    "CircuitBreakerCreated",
    "ContextChanged",
    "CircuitBreakerFailed",
    "CircuitBreakerRecovered",
    "AbstractUnitOfWork",
    "InMemoryUnitOfWork",
    "RedisUnitOfWork",
]
