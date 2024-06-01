"""
Provides a traceset implementation based on Python's pickle format.

This implementation of the traceset is thus very generic.
"""
import pickle
from io import BufferedIOBase, RawIOBase
from pathlib import Path
from typing import Union, BinaryIO

from public import public

from pyecsca.sca.trace_set.base import TraceSet


@public
class PickleTraceSet(TraceSet):
    """Pickle-based traceset format."""

    @classmethod
    def read(cls, input: Union[str, Path, bytes, BinaryIO], **kwargs) -> "PickleTraceSet":
        if isinstance(input, bytes):
            return pickle.loads(input)  # pickle is OK here, skipcq: BAN-B301
        elif isinstance(input, (str, Path)):
            with open(input, "rb") as f:
                return pickle.load(f)  # pickle is OK here, skipcq: BAN-B301
        elif isinstance(input, (RawIOBase, BufferedIOBase, BinaryIO)):
            return pickle.load(input)  # pickle is OK here, skipcq: BAN-B301
        raise TypeError

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, BinaryIO], **kwargs) -> "PickleTraceSet":
        raise NotImplementedError

    def write(self, output: Union[str, Path, BinaryIO]):
        if isinstance(output, (str, Path)):
            with open(output, "wb") as f:
                pickle.dump(self, f)
        elif isinstance(output, (RawIOBase, BufferedIOBase, BinaryIO)):
            pickle.dump(self, output)
        else:
            raise TypeError

    def __repr__(self):
        args = ", ".join(
            [f"{key}={getattr(self, key)!r}" for key in self._keys]
        )
        return f"PickleTraceSet(num_traces={len(self)}, {args})"
