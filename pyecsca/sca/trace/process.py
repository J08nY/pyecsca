"""Provides functions for sample-wise processing of single traces."""
from typing import cast

import numpy as np
from public import public

from .trace import Trace


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


def _rolling_window(samples: np.ndarray, window: int) -> np.ndarray:
    shape = samples.shape[:-1] + (samples.shape[-1] - window + 1, window)
    strides = samples.strides + (samples.strides[-1],)
    return np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)  # type: ignore[attr-defined]


@public
def rolling_mean(trace: Trace, window: int) -> Trace:
    """
    Compute the rolling mean of :paramref:`~.rolling_mean.trace` using :paramref:`~.rolling_mean.window`.

    Shortens the trace by ``window - 1``.

    :param trace:
    :param window:
    :return:
    """
    return trace.with_samples(
        cast(
            np.ndarray,
            np.mean(_rolling_window(trace.samples, window), -1).astype(
                dtype=trace.samples.dtype, copy=False
            ),
        )
    )


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
