from dataclasses import dataclass

import pytest

from purgatory.domain.messages import Command, Event
from purgatory.service.messagebus import ConfigurationError
from purgatory.service.unit_of_work import InMemoryUnitOfWork


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


class FakeUnitOfWorkWithDummyEvents(InMemoryUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events = []

    def collect_new_events(self):
        while self.events:
            yield self.events.pop(0)


async def listen_command(cmd: DummyCommand, uow: FakeUnitOfWorkWithDummyEvents):
    """This command raise an event played by the message bus."""
    uow.events.append(DummyEvent(id="", increment=10))


async def listen_event(cmd: DummyEvent, uow):
    """This event is indented to be fire by the message bus."""
    DummyModel.counter += cmd.increment


@pytest.mark.asyncio
async def test_messagebus(messagebus):
    """
    Test that the message bus is firing command and event.

    Because we use venusian, the bus only works the event as been
    attached.
    """

    DummyModel.counter = 0
    uow = FakeUnitOfWorkWithDummyEvents()
    await listen_command(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 0
    ), "Events raised cannot be played before the attach_listener has been called"

    await listen_event(DummyEvent(id="", increment=1), uow)
    assert DummyModel.counter == 1

    await messagebus.handle(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 1
    ), "The command cannot raise event before attach_listener"

    messagebus.add_listener(DummyCommand, listen_command)
    messagebus.add_listener(DummyEvent, listen_event)

    uow = FakeUnitOfWorkWithDummyEvents()
    await messagebus.handle(DummyCommand(id=""), uow)
    assert DummyModel.counter == 11, (
        "The command should raise an event that is handle by the bus that "
        "will increment the model to 10"
    )

    messagebus.remove_listener(DummyEvent, listen_event)

    uow = FakeUnitOfWorkWithDummyEvents()
    await messagebus.handle(DummyCommand(id=""), uow)
    assert (
        DummyModel.counter == 11
    ), "The command should raise an event that is not handled anymore "


@pytest.mark.asyncio
async def test_messagebus_handle_only_message(messagebus):
    class Msg:
        def __repr__(self):
            return "<msg>"

    with pytest.raises(RuntimeError) as ctx:
        await messagebus.handle(Msg(), FakeUnitOfWorkWithDummyEvents())
    assert str(ctx.value) == "<msg> was not an Event or Command"


@pytest.mark.asyncio
async def test_messagebus_cannot_register_handler_twice(messagebus):

    messagebus.add_listener(DummyCommand, listen_command)
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.add_listener(DummyCommand, listen_command)
    assert (
        str(ctx.value)
        == "<class 'tests.unittests.test_messagebus.DummyCommand'> command "
        "has been registered twice"
    )
    messagebus.remove_listener(DummyCommand, listen_command)
    messagebus.add_listener(DummyCommand, listen_command)


@pytest.mark.asyncio
async def test_messagebus_cannot_register_handler_on_non_message(messagebus):
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.add_listener(object, listen_command)
    assert (
        str(ctx.value)
        == "Invalid usage of the listen decorator: type <class 'object'> "
        "should be a command or an event"
    )


@pytest.mark.asyncio
async def test_messagebus_cannot_unregister_non_unregistered_handler(messagebus):
    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(DummyCommand, listen_command)
    assert (
        str(ctx.value)
        == "<class 'tests.unittests.test_messagebus.DummyCommand'> command "
        "has not been registered"
    )

    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(DummyEvent, listen_event)

    assert (
        str(ctx.value)
        == "<class 'tests.unittests.test_messagebus.DummyEvent'> event "
        "has not been registered"
    )

    with pytest.raises(ConfigurationError) as ctx:
        messagebus.remove_listener(object, listen_command)

    assert (
        str(ctx.value)
        == "Invalid usage of the listen decorator: type <class 'object'> "
        "should be a command or an event"
    )
