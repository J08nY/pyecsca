import weakref
from numpy import ndarray
from typing import Optional, Sequence

from public import public


@public
class Trace(object):
    """A power trace, which has an optional title, optional data bytes and mandatory samples."""

    def __init__(self, title: Optional[str], data: Optional[bytes],
                 samples: ndarray, trace_set=None):
        self.title = title
        self.data = data
        self.samples = samples
        self.trace_set = trace_set

    @property
    def trace_set(self):
        if self._trace_set is None:
            return None
        return self._trace_set()

    @trace_set.setter
    def trace_set(self, trace_set):
        if trace_set is None:
            self._trace_set = None
        else:
            self._trace_set = weakref.ref(trace_set)

    def __repr__(self):
        return "Trace(title={!r}, data={!r}, samples={!r}, trace_set={!r})".format(
                self.title, self.data, self.samples, self.trace_set)


@public
class CombinedTrace(Trace):
    """A power trace that was combined from other traces, `parents`."""

    def __init__(self, title: Optional[str], data: Optional[bytes],
                 samples: ndarray, trace_set=None, parents: Sequence[Trace] = None):
        super().__init__(title, data, samples, trace_set=trace_set)
        self.parents = None
        if parents is not None:
            self.parents = weakref.WeakSet(parents)

    def __repr__(self):
        return "CombinedTrace(title={!r}, data={!r}, samples={!r}, trace_set={!r}, parents={})".format(
                self.title, self.data, self.samples, self.trace_set,
                self.parents)
