import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("aiobreak").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass


from .service.circuitbreaker import CircuitBreakerFactory

__all__ = ["CircuitBreakerFactory"]
