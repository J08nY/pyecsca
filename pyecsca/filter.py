from copy import copy
from public import public
from scipy.signal import butter, lfilter
from typing import Union, Tuple

from .trace import Trace


def filter_any(trace: Trace, sampling_frequency: int,
               cutoff: Union[int, Tuple[int, int]], type: str) -> Trace:
    nyq = 0.5 * sampling_frequency
    if not isinstance(cutoff, int):
        normal_cutoff = tuple(map(lambda x: x / nyq, cutoff))
    else:
        normal_cutoff = cutoff / nyq
    b, a = butter(6, normal_cutoff, btype=type, analog=False)
    result_samples = lfilter(b, a, trace.samples)
    return Trace(copy(trace.title), copy(trace.data), result_samples)


@public
def filter_lowpass(trace: Trace, sampling_frequency: int, cutoff: int) -> Trace:
    return filter_any(trace, sampling_frequency, cutoff, "lowpass")


@public
def filter_highpass(trace: Trace, sampling_frequency: int, cutoff: int) -> Trace:
    return filter_any(trace, sampling_frequency, cutoff, "highpass")


@public
def filter_bandpass(trace: Trace, sampling_frequency: int, low: int, high: int) -> Trace:
    return filter_any(trace, sampling_frequency, (low, high), "bandpass")


@public
def filter_bandstop(trace: Trace, sampling_frequency: int, low: int, high: int) -> Trace:
    return filter_any(trace, sampling_frequency, (low, high), "bandstop")
