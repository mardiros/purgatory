"""
Message base classes.

`Command` and `Event` are two types used to handle changes in the model.

"""


class Message:
    """Base class for messaging."""


class Command(Message):
    """Baseclass for message of type command."""


class Event(Message):
    """Baseclass for message of type event."""
