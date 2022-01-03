"""
Propagate commands and events to every registered handles.

"""
import logging
from typing import Any

from purgatory.domain.messages.base import Command, Event, Message
from purgatory.service.messagebus import MessageRegistry

from . import unit_of_work

log = logging.getLogger(__name__)


class SyncMessageRegistry(MessageRegistry):
    """Store all the handlers for commands an events."""

    def handle(self, message: Message, uow: unit_of_work.SyncAbstractUnitOfWork) -> Any:
        """
        Notify listener of that event registered with `messagebus.add_listener`.
        Return the first event from the command.
        """
        queue = [message]
        ret = None
        while queue:
            message = queue.pop(0)
            if not isinstance(message, (Command, Event)):
                raise RuntimeError(f"{message} was not an Event or Command")
            msg_type = type(message)
            if msg_type in self.commands_registry:
                cmdret = self.commands_registry[msg_type](message, uow)
                if ret is None:
                    ret = cmdret
                queue.extend(uow.collect_new_events())
            elif msg_type in self.events_registry:
                for callback in self.events_registry[msg_type]:
                    callback(message, uow)
                    queue.extend(uow.collect_new_events())
        return ret
