import numpy as np
from copy import copy
from public import public
from scipy.signal import decimate

from .trace import Trace


@public
def downsample_average(trace: Trace, factor: int = 2) -> Trace:
    """
    Downsample samples of `trace` by `factor` by averaging `factor` consecutive samples in
    non-intersecting windows.

    :param trace:
    :param factor:
    :return:
    """
    resized = np.resize(trace.samples, len(trace.samples) - (len(trace.samples) % factor))
    result_samples = resized.reshape(-1, factor).mean(axis=1).astype(trace.samples.dtype)
    return Trace(result_samples, copy(trace.title), copy(trace.data))


@public
def downsample_pick(trace: Trace, factor: int = 2, offset: int = 0) -> Trace:
    """
    Downsample samples of `trace` by `factor` by picking each `factor`-th sample, starting at `offset`.

    :param trace:
    :param factor:
    :param offset:
    :return:
    """
    result_samples = trace.samples[offset::factor].copy()
    return Trace(result_samples, copy(trace.title), copy(trace.data))


@public
def downsample_decimate(trace: Trace, factor: int = 2) -> Trace:
    """
    Downsample samples of `trace` by `factor` by decimating.

    :param trace:
    :param factor:
    :return:
    """
    result_samples = decimate(trace.samples, factor)
    return Trace(result_samples, copy(trace.title), copy(trace.data))
