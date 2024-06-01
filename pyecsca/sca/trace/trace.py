"""Provides the Trace class."""
import weakref
from typing import Any, Mapping, Sequence, Optional
from copy import copy, deepcopy

from numpy import ndarray
import numpy as np
from numpy.typing import DTypeLike
from public import public


@public
class Trace:
    """Trace, which has some samples and metadata."""

    meta: Mapping[str, Any]
    samples: ndarray

    def __init__(
        self,
        samples: ndarray,
        meta: Optional[Mapping[str, Any]] = None,
        trace_set: Any = None,
    ):
        """
        Construct a new trace.

        :param samples: The sample array of the trace.
        :param meta: Metadata associated with the trace.
        :param trace_set: A trace set the trace is contained in.
        """
        if meta is None:
            meta = {}
        self.meta = meta
        self.samples = samples
        self.trace_set = trace_set

    def __len__(self):
        """Length of the trace, in samples."""
        return len(self.samples)

    def __getitem__(self, index):
        """Get the sample at `index`."""
        return self.samples[index]

    def __setitem__(self, key, value):
        """Set the sample at `key`."""
        self.samples[key] = value

    def __iter__(self):
        """Iterate over the samples."""
        yield from self.samples

    @property
    def trace_set(self) -> Any:
        """Return the trace set this trace is contained in, if any."""
        if self._trace_set is None:
            return None
        return self._trace_set()

    @trace_set.setter
    def trace_set(self, trace_set: Any):
        """Set the trace set of this trace."""
        if trace_set is None:
            self._trace_set = None
        else:
            self._trace_set = weakref.ref(trace_set)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_trace_set"] = None
        return state

    def __setstate__(self, state):
        self._trace_set = None
        self.__dict__.update(state)

    def __eq__(self, other):
        if not isinstance(other, Trace):
            return False
        return np.array_equal(self.samples, other.samples) and self.meta == other.meta

    def __hash__(self):
        # This will have collisions, but those can be sorted out by the equality check above.
        return hash((str(self.samples), tuple(self.meta.items())))

    def with_samples(self, samples: ndarray) -> "Trace":
        """
        Construct a copy of this trace, with the same metadata, but samples replaced by `samples`.

        :param samples: The samples of the new trace.
        :return: The new trace.
        """
        return Trace(samples, deepcopy(self.meta))

    def astype(self, dtype: DTypeLike) -> "Trace":
        """
        Construct a copy of this trace, with the same samples retyped using `dtype`.

        :param dtype: The numpy dtype.
        :return: The new trace
        """
        return self.with_samples(np.array(self.samples.astype(dtype)))

    def __copy__(self):
        return Trace(copy(self.samples), copy(self.meta), copy(self.trace_set))

    def __deepcopy__(self, memodict):
        return Trace(
            deepcopy(self.samples, memo=memodict)
            if isinstance(self.samples, np.ndarray)
            else np.array(self.samples),
            deepcopy(self.meta, memo=memodict),
        )

    def __repr__(self):
        return f"Trace(samples={self.samples!r}, trace_set={self.trace_set!r})"


@public
class CombinedTrace(Trace):
    """Trace that was combined from other traces, :paramref:`~.CombinedTrace.parents`."""

    def __init__(
        self,
        samples: ndarray,
        meta: Optional[Mapping[str, Any]] = None,
        trace_set: Any = None,
        parents: Optional[Sequence[Trace]] = None,
    ):
        super().__init__(samples, meta, trace_set=trace_set)
        self.parents = None
        if parents is not None:
            self.parents = weakref.WeakSet(parents)

    def __repr__(self):
        return f"CombinedTrace(samples={self.samples!r}, trace_set={self.trace_set!r}, parents={self.parents})"
