import numpy as np
from copy import copy
from public import public
from scipy.signal import decimate

from .trace import Trace


@public
def downsample_average(trace: Trace, factor: int = 2) -> Trace:
    resized = np.resize(trace.samples, len(trace.samples) - (len(trace.samples) % factor))
    result_samples = resized.reshape(-1, factor).mean(axis=1).astype(trace.samples.dtype)
    return Trace(copy(trace.title), copy(trace.data), result_samples)


@public
def downsample_pick(trace: Trace, factor: int = 2, offset: int = 0) -> Trace:
    result_samples = trace.samples[offset::factor].copy()
    return Trace(copy(trace.title), copy(trace.data), result_samples)


@public
def downsample_decimate(trace: Trace, factor: int = 2) -> Trace:
    result_samples = decimate(trace.samples, factor)
    return Trace(copy(trace.title), copy(trace.data), result_samples)
