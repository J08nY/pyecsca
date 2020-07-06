import numpy as np
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
    result_samples = resized.reshape(-1, factor).mean(axis=1).astype(trace.samples.dtype, copy=False)
    return trace.with_samples(result_samples)


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
    return trace.with_samples(result_samples)


@public
def downsample_max(trace: Trace, factor: int = 2) -> Trace:
    """
    Downsample samples of `trace` by `factor` by taking the maximum out of `factor` consecutive samples in
    non-intersecting windows.

    :param trace:
    :param factor:
    :return:
    """
    resized = np.resize(trace.samples, len(trace.samples) - (len(trace.samples) % factor))
    result_samples = resized.reshape(-1, factor).max(axis=1).astype(trace.samples.dtype, copy=False)
    return trace.with_samples(result_samples)


@public
def downsample_min(trace: Trace, factor: int = 2) -> Trace:
    """
    Downsample samples of `trace` by `factor` by taking the minimum out of `factor` consecutive samples in
    non-intersecting windows.

    :param trace:
    :param factor:
    :return:
    """
    resized = np.resize(trace.samples, len(trace.samples) - (len(trace.samples) % factor))
    result_samples = resized.reshape(-1, factor).min(axis=1).astype(trace.samples.dtype, copy=False)
    return trace.with_samples(result_samples)


@public
def downsample_decimate(trace: Trace, factor: int = 2) -> Trace:
    """
    Downsample samples of `trace` by `factor` by decimating.

    :param trace:
    :param factor:
    :return:
    """
    result_samples = decimate(trace.samples, factor)
    return trace.with_samples(result_samples)
