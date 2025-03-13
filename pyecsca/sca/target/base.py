"""Provides an abstract base class for targets."""

from abc import ABC, abstractmethod

from public import public


@public
class Target(ABC):
    """A target."""

    @abstractmethod
    def connect(self):
        """Connect to the target device."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        """Disconnect from the target device."""
        raise NotImplementedError
