from public import public
from typing import List

from ..trace import Trace


@public
class TraceSet(object):
    _traces: List = []
    _keys: List = []

    def __init__(self, *traces: Trace, **kwargs):
        self._traces = list(traces)
        self.__dict__.update(kwargs)
        self._keys = list(kwargs.keys())

    def __len__(self):
        return len(self._traces)

    def __getitem__(self, index) -> Trace:
        return self._traces[index]

    def __iter__(self):
        yield from self._traces

    def __repr__(self):
        args = ", ".join(["{}={!r}".format(key, getattr(self, key)) for key in
                          self._keys])
        return "TraceSet({})".format(args)
