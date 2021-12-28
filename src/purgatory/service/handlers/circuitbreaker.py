from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import CircuitBreakerStateChanged
from purgatory.domain.model import CircuitBreaker
from purgatory.service.unit_of_work import AbstractUnitOfWork


async def register_circuit_breaker(
    cmd: CreateCircuitBreaker, uow: AbstractUnitOfWork
) -> CircuitBreaker:
    ret = CircuitBreaker(cmd.name, cmd.threshold, cmd.ttl)
    await uow.circuit_breakers.register(ret)
    return ret


async def save_circuit_breaker_state(
    cmd: CircuitBreakerStateChanged, uow: AbstractUnitOfWork
) -> None:
    await uow.circuit_breakers.update_state(
        cmd.name, cmd.state, cmd.opened_at
    )
