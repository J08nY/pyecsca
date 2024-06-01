"""Provides functions for sample-wise processing of single traces."""
from typing import Any

import numpy as np
from scipy.signal import convolve
from public import public

from pyecsca.sca.trace.trace import Trace


@public
def absolute(trace: Trace) -> Trace:
    """
    Apply absolute value to samples of :paramref:`~.absolute.trace`.

    :param trace:
    :return:
    """
    return trace.with_samples(np.absolute(trace.samples))


@public
def invert(trace: Trace) -> Trace:
    """
    Invert(negate) the samples of :paramref:`~.invert.trace`.

    :param trace:
    :return:
    """
    return trace.with_samples(np.negative(trace.samples))


@public
def threshold(trace: Trace, value) -> Trace:
    """
    Map samples of the :paramref:`~.threshold.trace` to ``1`` if they are above :paramref:`~.threshold.value` or to ``0``.

    :param trace:
    :param value:
    :return:
    """
    result_samples = trace.samples.copy()
    result_samples[result_samples <= value] = 0
    result_samples[np.nonzero(result_samples)] = 1
    return trace.with_samples(result_samples)


@public
def rolling_mean(trace: Trace, window: int) -> Trace:
    """
    Compute the rolling mean of :paramref:`~.rolling_mean.trace` using :paramref:`~.rolling_mean.window`.

    Shortens the trace by ``window - 1``.

    :param trace:
    :param window:
    :return:
    """
    return trace.with_samples(convolve(trace.samples, np.ones(window, dtype=trace.samples.dtype), "valid") / window)


@public
def offset(trace: Trace, offset) -> Trace:
    """
    Offset samples of :paramref:`~.offset.trace` by :paramref:`~.offset.offset`, sample-wise.

    Adds :paramref:`~.offset.offset` to all samples.

    :param trace:
    :param offset:
    :return:
    """
    return trace.with_samples(trace.samples + offset)


def _root_mean_square(trace: Trace):
    return np.sqrt(np.mean(np.square(trace.samples)))


@public
def recenter(trace: Trace) -> Trace:
    """
    Subtract the root mean square of the :paramref:`~.recenter.trace` from its samples, sample-wise.

    :param trace:
    :return:
    """
    around = _root_mean_square(trace)
    return offset(trace, -around)


@public
def normalize(trace: Trace) -> Trace:
    """
    Normalize a :paramref:`~.normalize.trace` by subtracting its mean and dividing by its standard deviation.

    :param trace:
    :return:
    """
    return trace.with_samples(
        (trace.samples - np.mean(trace.samples)) / np.std(trace.samples)
    )


@public
def normalize_wl(trace: Trace) -> Trace:
    """
    Normalize a :paramref:`~.normalize_wl.trace` by subtracting its mean and dividing by a multiple (= ``len(trace)``) of its standard deviation.

    :param trace:
    :return:
    """
    return trace.with_samples(
        (trace.samples - np.mean(trace.samples))
        / (np.std(trace.samples) * len(trace.samples))
    )


@public
def transform(trace: Trace, min_value: Any = 0, max_value: Any = 1) -> Trace:
    """
    Scale a :paramref:`~.transform.trace` so that its minimum is at :paramref:`~.transform.min_value` and its maximum is at :paramref:`~.transform.max_value`.

    :param trace:
    :param min_value:
    :param max_value:
    :return:
    """
    t_min = np.min(trace.samples)
    t_max = np.max(trace.samples)
    t_range = t_max - t_min
    d = max_value - min_value
    return trace.with_samples(((trace.samples - t_min) * (d/t_range)) + min_value)
