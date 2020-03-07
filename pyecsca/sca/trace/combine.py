from typing import Callable, Optional

import numpy as np
from public import public

from .trace import Trace, CombinedTrace


@public
def average(*traces: Trace) -> Optional[CombinedTrace]:
    """
    Average `traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        return None
    if len(traces) == 1:
        return CombinedTrace(traces[0].samples.copy())
    dtype = traces[0].samples.dtype
    result_samples = np.mean(np.array([trace.samples for trace in traces]), axis=0).astype(dtype)
    return CombinedTrace(result_samples)


@public
def conditional_average(*traces: Trace, condition: Callable[[Trace], bool]) -> Optional[
    CombinedTrace]:
    """
    Average `traces` for which the `condition` is True, sample-wise.

    :param traces:
    :param condition:
    :return:
    """
    return average(*filter(condition, traces))


@public
def standard_deviation(*traces: Trace) -> Optional[CombinedTrace]:
    """
    Compute the standard-deviation of the `traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        return None
    dtype = traces[0].samples.dtype
    result_samples = np.std(np.array([trace.samples for trace in traces]), axis=0).astype(dtype)
    return CombinedTrace(result_samples)


@public
def subtract(one: Trace, other: Trace) -> CombinedTrace:
    """
    Subtract `other` from `one`, sample-wise.

    :param one:
    :param other:
    :return:
    """
    result_samples = one.samples - other.samples
    return CombinedTrace(result_samples)
