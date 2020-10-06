import pickle
from io import BufferedIOBase, RawIOBase
from pathlib import Path
from typing import Union, BinaryIO

from public import public

from .base import TraceSet


@public
class PickleTraceSet(TraceSet):
    @classmethod
    def read(cls, input: Union[str, Path, bytes, BinaryIO]) -> "PickleTraceSet":
        if isinstance(input, bytes):
            return pickle.loads(input)
        elif isinstance(input, (str, Path)):
            with open(input, "rb") as f:
                return pickle.load(f)
        elif isinstance(input, (RawIOBase, BufferedIOBase, BinaryIO)):
            return pickle.load(input)
        raise TypeError

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, BinaryIO]) -> "PickleTraceSet":
        raise NotImplementedError

    def write(self, output: Union[str, Path, BinaryIO]):
        if isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                pickle.dump(self, f)
        elif isinstance(output, (RawIOBase, BufferedIOBase, BinaryIO)):
            pickle.dump(self, output)
        else:
            raise TypeError
