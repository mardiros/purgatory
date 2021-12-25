from dataclasses import dataclass

from aiobreak.domain.messages import Command, Event
from aiobreak.service import messagebus

from aiobreak.service.unit_of_work import _InMemoryUnitOfWork


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


class FakeUnitOfWorkWithDummyEvents(_InMemoryUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events = []

    def collect_new_events(self):
        while self.events:
            yield self.events.pop(0)


def listen_command(cmd: DummyCommand, uow):
    """This command raise an event played by the message bus."""
    uow.events.append(DummyEvent(id="", increment=10))


def listen_event(cmd: DummyEvent, uow):
    """This event is indented to be fire by the message bus."""
    DummyModel.counter += cmd.increment


def test_messagebus():
    """
    Test that the message bus is firing command and event.

    Because we use venusian, the bus only works the event as been
    attached.
    """

    DummyModel.counter = 0
    with FakeUnitOfWorkWithDummyEvents() as uow:
        listen_command(DummyCommand(id=""), uow)
        assert DummyModel.counter == 0, (
            "Events raised cannot be played before the "
            "attach_listener has been called"
        )

        listen_event(DummyEvent(id="", increment=1), uow)
        assert DummyModel.counter == 1

        messagebus.handle(DummyCommand(id=""), uow)
        assert (
            DummyModel.counter == 1
        ), "The command cannot raise event before attach_listener"

    messagebus.add_listener(DummyCommand, listen_command)
    messagebus.add_listener(DummyEvent, listen_event)

    with FakeUnitOfWorkWithDummyEvents() as uow:
        messagebus.handle(DummyCommand(id=""), uow)
        assert DummyModel.counter == 11, (
            "The command should raise an event that is handle by the bus that "
            "will increment the model to 10"
        )

    messagebus.remove_listener(DummyEvent, listen_event)

    with FakeUnitOfWorkWithDummyEvents() as uow:
        messagebus.handle(DummyCommand(id=""), uow)
        assert (
            DummyModel.counter == 11
        ), "The command should raise an event that is not handled anymore "
