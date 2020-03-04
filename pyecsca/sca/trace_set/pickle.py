import pickle
from io import BufferedIOBase, RawIOBase, IOBase
from pathlib import Path
from typing import Union

from public import public

from .base import TraceSet


@public
class PickleTraceSet(TraceSet):
    @classmethod
    def read(cls, input: Union[str, Path, bytes, RawIOBase, BufferedIOBase]) -> "PickleTraceSet":
        if isinstance(input, bytes):
            return pickle.loads(input)
        elif isinstance(input, (str, Path)):
            with open(input, "rb") as f:
                return pickle.load(f)
        elif isinstance(input, IOBase):
            return pickle.load(input)
        raise ValueError

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, RawIOBase, BufferedIOBase]) -> "PickleTraceSet":
        raise NotImplementedError

    def write(self, output: Union[str, Path, RawIOBase, BufferedIOBase]):
        if isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                pickle.dump(self, f)
        elif isinstance(output, IOBase):
            pickle.dump(self, output)
        else:
            raise ValueError
