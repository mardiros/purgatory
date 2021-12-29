from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerStateChanged,
)
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
    await uow.circuit_breakers.update_state(cmd.name, cmd.state, cmd.opened_at)


async def inc_circuit_breaker_failure(
    cmd: CircuitBreakerFailed, uow: AbstractUnitOfWork
) -> None:
    await uow.circuit_breakers.inc_failures(cmd.name, cmd.failure_count)
