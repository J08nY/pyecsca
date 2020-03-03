from abc import abstractmethod
from typing import Optional

from public import public

from .base import Target


@public
class SerialTarget(Target):

    @abstractmethod
    def write(self, data: bytes):
        ...

    @abstractmethod
    def read(self, num: int = 0, timeout: int = 0) -> bytes:
        ...
