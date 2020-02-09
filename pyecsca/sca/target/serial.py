from public import public

from .base import Target


@public
class SerialTarget(Target):

    def write(self, data: bytes):
        raise NotImplementedError

    def read(self, timeout: int) -> bytes:
        raise NotImplementedError
