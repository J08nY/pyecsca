from abc import ABC, abstractmethod

from public import public


@public
class Target(ABC):
    """A target."""

    @abstractmethod
    def connect(self):
        """Connect to the target device."""
        ...

    @abstractmethod
    def disconnect(self):
        """Disconnect from the target device."""
        ...
