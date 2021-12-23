from aiobreak.circuitbreaker import CircuitBreaker, CircuitBreakerFactory


def test_circuitbreaker_factory_decorator():

    count = 0
    circuitbreaker = CircuitBreakerFactory()

    @circuitbreaker(circuit="client")
    def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1

    fail_or_success()
    assert count == 1
    assert circuitbreaker.breakers == {
        "client": CircuitBreaker(name="client", threshold=5)
    }

    @circuitbreaker(circuit="client2", threshold=15)
    def _success2():
        pass

    assert circuitbreaker.breakers == {
        "client": CircuitBreaker(name="client", threshold=5),
        "client2": CircuitBreaker(name="client2", threshold=15),
    }


def test_circuitbreaker_factory_context():

    count = 0
    circuitbreaker = CircuitBreakerFactory()

    with circuitbreaker.get_breaker("my"):
        count += 1

    with circuitbreaker.get_breaker("my2", threshold=42):
        count += 1

    assert circuitbreaker.breakers == {
        "my": CircuitBreaker(name="my", threshold=5),
        "my2": CircuitBreaker(name="my2", threshold=42),
    }
