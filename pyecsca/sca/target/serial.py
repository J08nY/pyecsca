"""
This module provides an abstract serial target, that communicates by writing and reading a stream of bytes.
"""
from abc import abstractmethod

from public import public

from .base import Target


@public
class SerialTarget(Target):
    """A serial target."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """
        Write the `data` bytes to the target's serial input.

        :param data: The data to write.
        """
        ...

    @abstractmethod
    def read(self, num: int = 0, timeout: int = 0) -> bytes:
        """
        Read upto `num` bytes or until `timeout` milliseconds from the target's serial output.

        :param num: The number of bytes to read, `0` for all available.
        :param timeout: The timeout in milliseconds.
        :return: The bytes read.
        """
        ...
