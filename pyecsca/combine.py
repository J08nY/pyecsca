import numpy as np
from public import public
from typing import Callable, Optional

from .trace import Trace, CombinedTrace


@public
def average(*traces: Trace) -> Optional[CombinedTrace]:
    if not traces:
        return None
    if len(traces) == 1:
        return CombinedTrace(None, None, traces[0].samples.copy(), parents=traces)
    dtype = traces[0].samples.dtype
    result_samples = np.mean(np.array([trace.samples for trace in traces]), axis=0).astype(dtype)
    return CombinedTrace(None, None, result_samples, parents=traces)


@public
def conditional_average(*traces: Trace, condition: Callable[[Trace], bool]) -> Optional[CombinedTrace]:
    return average(*filter(condition, traces))


@public
def standard_deviation(*traces: Trace) -> Optional[CombinedTrace]:
    if not traces:
        return None
    dtype = traces[0].samples.dtype
    result_samples = np.std(np.array([trace.samples for trace in traces]), axis=0).astype(dtype)
    return CombinedTrace(None, None, result_samples, parents=traces)
