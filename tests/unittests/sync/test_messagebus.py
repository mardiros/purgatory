from dataclasses import dataclass

import pytest

from purgatory.domain.messages import Command, Event
from purgatory.service.messagebus import ConfigurationError
from purgatory.sync.unit_of_work import SyncInMemoryUnitOfWork


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


class SyncFakeUnitOfWorkWithDummyEvents(SyncInMemoryUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events = []

    def collect_new_events(self):
        while self.events:
            yield self.events.pop(0)


def listen_command(cmd: DummyCommand, uow: SyncFakeUnitOfWorkWithDummyEvents):
    """This command raise an event played by the message bus."""
    uow.events.append(DummyEvent(id="", increment=10))


def listen_event(cmd: DummyEvent, uow):
    """This event is indented to be fire by the message bus."""
    DummyModel.counter += cmd.increment


def test_messagebus(messagebus):
    """
    Test that the message bus is firing command and event.

    Because we use venusian, the bus only works the event as been
    attached.
    """

    DummyModel.counter = 0
    uow = SyncFakeUnitOfWorkWithDummyEvents()
    listen_command(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 0
    ), "Events raised cannot be played before the attach_listener has been called"

    listen_event(DummyEvent(id="", increment=1), uow)
    assert DummyModel.counter == 1

    messagebus.handle(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 1
    ), "The command cannot raise event before attach_listener"

    messagebus.add_listener(DummyCommand, listen_command)
    messagebus.add_listener(DummyEvent, listen_event)

    uow = SyncFakeUnitOfWorkWithDummyEvents()
    messagebus.handle(DummyCommand(id=""), uow)
    assert DummyModel.counter == 11, (
        "The command should raise an event that is handle by the bus that "
        "will increment the model to 10"
    )

    messagebus.remove_listener(DummyEvent, listen_event)

    uow = SyncFakeUnitOfWorkWithDummyEvents()
    messagebus.handle(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 11
    ), "The command should raise an event that is not handled anymore "


def test_messagebus_handle_only_message(messagebus):
    class Msg:
        def __repr__(self):
            return "<msg>"

    with pytest.raises(RuntimeError) as ctx:
        messagebus.handle(Msg(), SyncFakeUnitOfWorkWithDummyEvents())
    assert str(ctx.value) == "<msg> was not an Event or Command"


def test_messagebus_cannot_register_handler_twice(messagebus):

    messagebus.add_listener(DummyCommand, listen_command)
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.add_listener(DummyCommand, listen_command)
    assert (
        str(ctx.value)
        == "<class 'tests.unittests.sync.test_messagebus.DummyCommand'> command "
        "has been registered twice"
    )
    messagebus.remove_listener(DummyCommand, listen_command)
    messagebus.add_listener(DummyCommand, listen_command)


def test_messagebus_cannot_register_handler_on_non_message(messagebus):
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.add_listener(object, listen_command)
    assert (
        str(ctx.value)
        == "Invalid usage of the listen decorator: type <class 'object'> "
        "should be a command or an event"
    )


def test_messagebus_cannot_unregister_non_unregistered_handler(messagebus):
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(DummyCommand, listen_command)
    assert (
        str(ctx.value)
        == "<class 'tests.unittests.sync.test_messagebus.DummyCommand'> command "
        "has not been registered"
    )

    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(DummyEvent, listen_event)

    assert (
        str(ctx.value)
        == "<class 'tests.unittests.sync.test_messagebus.DummyEvent'> event "
        "has not been registered"
    )

    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(object, listen_command)

    assert (
        str(ctx.value)
        == "Invalid usage of the listen decorator: type <class 'object'> "
        "should be a command or an event"
    )
