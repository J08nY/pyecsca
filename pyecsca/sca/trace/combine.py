"""Provides functions for combining traces sample-wise."""
from typing import Callable, Tuple

import numpy as np
from public import public

from pyecsca.sca.trace.trace import Trace, CombinedTrace


@public
def average(*traces: Trace) -> CombinedTrace:
    """
    Average :paramref:`~.average.traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        raise ValueError("Nothing to combine")
    if len(traces) == 1:
        return CombinedTrace(traces[0].samples.copy())
    min_samples = min(map(len, traces))
    s = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        s = np.add(s, t.samples[:min_samples])
    avg = (1 / len(traces)) * s
    del s
    return CombinedTrace(avg)


@public
def conditional_average(
    *traces: Trace, condition: Callable[[Trace], bool]
) -> CombinedTrace:
    """
    Average :paramref:`~.conditional_average.traces` for which the :paramref:`~.conditional_average.condition` is ``True``, sample-wise.

    :param traces:
    :param condition:
    :return:
    """
    return average(*filter(condition, traces))


@public
def standard_deviation(*traces: Trace) -> CombinedTrace:
    """
    Compute the sample standard-deviation of the :paramref:`~.standard_deviation.traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        raise ValueError("Nothing to combine")
    if len(traces) == 1:
        return CombinedTrace(np.zeros(len(traces[0]), dtype=np.float64))
    min_samples = min(map(len, traces))
    s = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        s = np.add(s, t.samples[:min_samples])
    s = (1 / len(traces)) * s
    ts = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        d = np.subtract(t.samples[:min_samples], s)
        ts = np.add(ts, np.multiply(d, d, dtype=np.float64))
    std = np.sqrt((1 / (len(traces) - 1)) * ts)
    del s
    del ts
    return CombinedTrace(std)


@public
def variance(*traces: Trace) -> CombinedTrace:
    """
    Compute the sample variance of the :paramref:`~.variance.traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        raise ValueError("Nothing to combine")
    if len(traces) == 1:
        return CombinedTrace(np.zeros(len(traces[0]), dtype=np.float64))
    min_samples = min(map(len, traces))
    s = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        s = np.add(s, t.samples[:min_samples])
    s = (1 / len(traces)) * s
    ts = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        d = np.subtract(t.samples[:min_samples], s)
        ts = np.add(ts, np.multiply(d, d, dtype=np.float64))
    var = (1 / (len(traces) - 1)) * ts
    del s
    del ts
    return CombinedTrace(var)


@public
def average_and_variance(*traces) -> Tuple[CombinedTrace, CombinedTrace]:
    """
    Compute the average and sample variance of the :paramref:`~.average_and_variance.traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        raise ValueError("Nothing to combine")
    if len(traces) == 1:
        return (
            CombinedTrace(traces[0].samples.copy()),
            CombinedTrace(np.zeros(len(traces[0]), dtype=np.float64)),
        )
    min_samples = min(map(len, traces))
    s = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        s = np.add(s, t.samples[:min_samples])
    s = (1 / len(traces)) * s
    ts = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        d = np.subtract(t.samples[:min_samples], s)
        ts = np.add(ts, np.multiply(d, d, dtype=np.float64))
    var = (1 / (len(traces) - 1)) * ts
    del ts
    return (CombinedTrace(s), CombinedTrace(var))


@public
def add(*traces: Trace) -> CombinedTrace:
    """
    Add :paramref:`~.add.traces`, sample-wise.

    :param traces:
    :return:
    """
    if not traces:
        raise ValueError("Nothing to combine")
    if len(traces) == 1:
        return CombinedTrace(traces[0].samples.copy())
    min_samples = min(map(len, traces))
    s = np.zeros(min_samples, dtype=np.float64)
    for t in traces:
        s = np.add(s, t.samples[:min_samples])
    return CombinedTrace(s)


@public
def subtract(one: Trace, other: Trace) -> CombinedTrace:
    """
    Subtract :paramref:`~.subtract.other` from :paramref:`~.subtract.one`, sample-wise.

    :param one:
    :param other:
    :return:
    """
    return CombinedTrace(np.subtract(one.samples, other.samples))
