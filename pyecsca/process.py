import numpy as np
from copy import copy
from public import public

from .trace import Trace


@public
def absolute(trace: Trace) -> Trace:
    return Trace(copy(trace.title), copy(trace.data), np.absolute(trace.samples))


@public
def invert(trace: Trace) -> Trace:
    return Trace(copy(trace.title), copy(trace.data), np.negative(trace.samples))


@public
def threshold(trace: Trace, value) -> Trace:
    result_samples = trace.samples.copy()
    result_samples[result_samples <= value] = 0
    result_samples[np.nonzero(result_samples)] = 1
    return Trace(copy(trace.title), copy(trace.data), result_samples)


def rolling_window(samples: np.ndarray, window: int) -> np.ndarray:
    shape = samples.shape[:-1] + (samples.shape[-1] - window + 1, window)
    strides = samples.strides + (samples.strides[-1],)
    return np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)


@public
def rolling_mean(trace: Trace, window: int) -> Trace:
    return Trace(copy(trace.title), copy(trace.data),
                 np.mean(rolling_window(trace.samples, window), -1).astype(
                     dtype=trace.samples.dtype))


@public
def offset(trace: Trace, offset) -> Trace:
    return Trace(copy(trace.title), copy(trace.data), trace.samples + offset)


def root_mean_square(trace: Trace):
    return np.sqrt(np.mean(np.square(trace.samples)))


@public
def recenter(trace: Trace) -> Trace:
    around = root_mean_square(trace)
    return offset(trace, -around)


@public
def normalize(trace: Trace) -> Trace:
    return Trace(copy(trace.title), copy(trace.data),
                 (trace.samples - np.mean(trace.samples)) / np.std(trace.samples))


@public
def normalize_wl(trace: Trace) -> Trace:
    return Trace(copy(trace.title), copy(trace.data),
                 (trace.samples - np.mean(trace.samples)) / (
                             np.std(trace.samples) * len(trace.samples)))
