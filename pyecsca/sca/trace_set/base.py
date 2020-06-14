from io import RawIOBase, BufferedIOBase
from pathlib import Path
from typing import List, Union, BinaryIO

from public import public

from ..trace import Trace


@public
class TraceSet(object):
    _traces: List[Trace]
    _keys: List

    def __init__(self, *traces: Trace, **kwargs):
        self._traces = list(traces)
        for trace in self._traces:
            trace.trace_set = self
        self.__dict__.update(kwargs)
        self._keys = list(kwargs.keys())

    def __len__(self):
        """Return the number of traces."""
        return len(self._traces)

    def __getitem__(self, index) -> Trace:
        """Get the trace at `index`."""
        return self._traces[index]

    def __iter__(self):
        """Iterate over the traces."""
        yield from self._traces

    @classmethod
    def read(cls, input: Union[str, Path, bytes, BinaryIO]) -> "TraceSet":
        raise NotImplementedError

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, BinaryIO]) -> "TraceSet":
        raise NotImplementedError

    def write(self, output: Union[str, Path, BinaryIO]):
        raise NotImplementedError

    def __repr__(self):
        args = ", ".join(["{}={!r}".format(key, getattr(self, key)) for key in
                          self._keys])
        return "TraceSet({})".format(args)
