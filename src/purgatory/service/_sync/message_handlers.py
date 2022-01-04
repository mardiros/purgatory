from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context
from purgatory.service._sync.unit_of_work import SyncAbstractUnitOfWork


def register_circuit_breaker(
    cmd: CreateCircuitBreaker, uow: SyncAbstractUnitOfWork
) -> Context:
    """
    Register circuit breaker in the repository

    when receiving the CreateCircuitBreaker command.
    """
    ret = Context(cmd.name, cmd.threshold, cmd.ttl)
    uow.contexts.register(ret)
    uow.contexts.messages.append(
        CircuitBreakerCreated(cmd.name, cmd.threshold, cmd.ttl)
    )
    return ret


def save_circuit_breaker_state(
    evt: ContextChanged, uow: SyncAbstractUnitOfWork
) -> None:
    """
    Save the circuit breaker state in the repository

    when receiving the ContextChanged event.
    """
    uow.contexts.update_state(evt.name, evt.state, evt.opened_at)


def inc_circuit_breaker_failure(
    evt: CircuitBreakerFailed, uow: SyncAbstractUnitOfWork
) -> None:
    """
    Increment the number of failure in the repository

    when receiving the CircuitBreakerFailed event.
    """
    uow.contexts.inc_failures(evt.name, evt.failure_count)


def reset_failure(evt: CircuitBreakerRecovered, uow: SyncAbstractUnitOfWork) -> None:
    """
    Reset the number of failure in the repository

    when receiving the CircuitBreakerRecovered event.
    """
    uow.contexts.reset_failure(evt.name)
