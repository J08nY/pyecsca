import weakref
from numpy import ndarray
from typing import Optional, Sequence


class Trace(object):

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


class CombinedTrace(Trace):

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
