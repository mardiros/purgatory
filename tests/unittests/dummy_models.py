from dataclasses import dataclass
from purgatory.domain.messages import Command, Event


class DummyModel:
    """A dummy model that will be updated using an event."""

    counter = 0


@dataclass
class DummyCommand(Command):
    id: str


@dataclass
class DummyEvent(Event):
    id: str
    increment: int
