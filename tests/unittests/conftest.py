from purgatory import CircuitBreakerFactory
from purgatory.domain.repository import InMemoryRepository

def circuitbreaker_factory():
    yield CircuitBreakerFactory()
