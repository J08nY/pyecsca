import weakref
from numpy import ndarray
from public import public
from typing import Optional, Sequence, Any


@public
class Trace(object):
    """A power trace, which has an optional title, optional data bytes and mandatory samples."""
    title: Optional[str]
    data: Optional[bytes]
    samples: ndarray

    def __init__(self, samples: ndarray, title: Optional[str], data: Optional[bytes],
                 trace_set: Any = None):
        self.title = title
        self.data = data
        self.samples = samples
        self.trace_set = trace_set

    @property
    def trace_set(self) -> Any:
        if self._trace_set is None:
            return None
        return self._trace_set()

    @trace_set.setter
    def trace_set(self, trace_set: Any):
        if trace_set is None:
            self._trace_set = None
        else:
            self._trace_set = weakref.ref(trace_set)

    def __repr__(self):
        return f"Trace(title={self.title!r}, data={self.data!r}, samples={self.samples!r}, trace_set={self.trace_set!r})"


@public
class CombinedTrace(Trace):
    """A power trace that was combined from other traces, `parents`."""

    def __init__(self, samples: ndarray, title: Optional[str], data: Optional[bytes],
                 trace_set=None, parents: Sequence[Trace] = None):
        super().__init__(samples, title, data, trace_set=trace_set)
        self.parents = None
        if parents is not None:
            self.parents = weakref.WeakSet(parents)

    def __repr__(self):
        return f"CombinedTrace(title={self.title!r}, data={self.data!r}, samples={self.samples!r}, trace_set={self.trace_set!r}, parents={self.parents})"
