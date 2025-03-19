import numpy as np
from public import public
from typing import Any, Mapping, Sequence, Optional

from pyecsca.sca.trace_set.base import TraceSet


@public
class StackedTraces:
    """Samples of multiple traces and metadata"""

    meta: Mapping[str, Any]
    samples: np.ndarray

    # TODO: Split metadata into common and per-trace
    def __init__(
        self, samples: np.ndarray, meta: Optional[Mapping[str, Any]] = None
    ) -> None:
        if meta is None:
            meta = {}
        self.meta = meta
        self.samples = samples

    @classmethod
    def fromarray(
        cls, traces: Sequence[np.ndarray], meta: Optional[Mapping[str, Any]] = None
    ) -> "StackedTraces":
        if meta is None:
            meta = {}
        ts = list(traces)
        min_samples = min(map(len, ts))
        for i, t in enumerate(ts):
            ts[i] = t[:min_samples]
        stacked = np.stack(ts)
        return cls(stacked, meta)

    @classmethod
    def fromtraceset(cls, traceset: TraceSet) -> "StackedTraces":
        traces = [t.samples for t in traceset]
        return cls.fromarray(traces)

    def __len__(self):
        return self.samples.shape[0]

    def __getitem__(self, index):
        return self.samples[index]

    def __iter__(self):
        yield from self.samples
