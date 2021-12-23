
from aiobreak.circuitbreaker import CircuitBreaker


def test_circuitbreaker_decorator():
    
    count = 0
    circuitbreaker = CircuitBreaker()

    @circuitbreaker(circuit="client")
    def fail_or_success(fail=False):
        if fail:
            raise RuntimeError("Boom")
        nonlocal count
        count += 1
    
    fail_or_success()
    assert count == 1
