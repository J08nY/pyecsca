"""Provides an abstract serial target, that communicates by writing and reading a stream of bytes."""
from abc import abstractmethod

from public import public

from pyecsca.sca.target.base import Target


@public
class SerialTarget(Target):
    """Serial target."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """
        Write the :paramref:`~.write.data` bytes to the target's serial input.

        :param data: The data to write.
        """
        raise NotImplementedError

    @abstractmethod
    def read(self, num: int = 0, timeout: int = 0) -> bytes:
        """
        Read upto :paramref:`~.read.num` bytes or until :paramref:`~.read.timeout` milliseconds from the target's serial output.

        :param num: The number of bytes to read, ``0`` for all available.
        :param timeout: The timeout in milliseconds.
        :return: The bytes read.
        """
        raise NotImplementedError
