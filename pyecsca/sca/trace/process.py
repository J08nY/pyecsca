import numpy as np
from public import public

from .trace import Trace


@public
def absolute(trace: Trace) -> Trace:
    """
    Apply absolute value to samples of `trace`.

    :param trace:
    :return:
    """
    return trace.with_samples(np.absolute(trace.samples))


@public
def invert(trace: Trace) -> Trace:
    """
    Invert(negate) the samples of `trace`.

    :param trace:
    :return:
    """
    return trace.with_samples(np.negative(trace.samples))


@public
def threshold(trace: Trace, value) -> Trace:
    """
    Map samples of the `trace` to 1 if they are above `value` or to 0.

    :param trace:
    :param value:
    :return:
    """
    result_samples = trace.samples.copy()
    result_samples[result_samples <= value] = 0
    result_samples[np.nonzero(result_samples)] = 1
    return trace.with_samples(result_samples)


def rolling_window(samples: np.ndarray, window: int) -> np.ndarray:
    shape = samples.shape[:-1] + (samples.shape[-1] - window + 1, window)
    strides = samples.strides + (samples.strides[-1],)
    return np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)


@public
def rolling_mean(trace: Trace, window: int) -> Trace:
    """
    Compute the rolling mean of `trace` using `window`. Shortens the trace by `window` - 1.

    :param trace:
    :param window:
    :return:
    """
    return trace.with_samples(np.mean(rolling_window(trace.samples, window), -1).astype(
            dtype=trace.samples.dtype, copy=False))


@public
def offset(trace: Trace, offset) -> Trace:
    """
    Offset samples of `trace` by `offset`, sample-wise (Adds `offset` to all samples).

    :param trace:
    :param offset:
    :return:
    """
    return trace.with_samples(trace.samples + offset)


def root_mean_square(trace: Trace):
    return np.sqrt(np.mean(np.square(trace.samples)))


@public
def recenter(trace: Trace) -> Trace:
    """
    Subtract the root mean square of the `trace` from its samples, sample-wise.

    :param trace:
    :return:
    """
    around = root_mean_square(trace)
    return offset(trace, -around)


@public
def normalize(trace: Trace) -> Trace:
    return trace.with_samples((trace.samples - np.mean(trace.samples)) / np.std(trace.samples))


@public
def normalize_wl(trace: Trace) -> Trace:
    return trace.with_samples((trace.samples - np.mean(trace.samples)) / (
            np.std(trace.samples) * len(trace.samples)))
