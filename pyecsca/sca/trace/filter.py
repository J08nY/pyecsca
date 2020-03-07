from public import public
from scipy.signal import butter, lfilter
from typing import Union, Tuple

from .trace import Trace


def filter_any(trace: Trace, sampling_frequency: int,
               cutoff: Union[int, Tuple[int, int]], band_type: str) -> Trace:
    nyq = 0.5 * sampling_frequency
    if not isinstance(cutoff, int):
        b, a = butter(6, tuple(map(lambda x: x / nyq, cutoff)), btype=band_type, analog=False, output='ba')
    else:
        b, a = butter(6, cutoff / nyq, btype=band_type, analog=False, output='ba')
    return trace.with_samples(lfilter(b, a, trace.samples))


@public
def filter_lowpass(trace: Trace, sampling_frequency: int, cutoff: int) -> Trace:
    """
    Apply a lowpass digital filter (Butterworth) to `trace`, given `sampling_frequency` and
    `cutoff` frequency.

    :param trace:
    :param sampling_frequency:
    :param cutoff:
    :return:
    """
    return filter_any(trace, sampling_frequency, cutoff, "lowpass")


@public
def filter_highpass(trace: Trace, sampling_frequency: int, cutoff: int) -> Trace:
    """
    Apply a highpass digital filter (Butterworth) to `trace`, given `sampling_frequency` and
    `cutoff` frequency.

    :param trace:
    :param sampling_frequency:
    :param cutoff:
    :return:
    """
    return filter_any(trace, sampling_frequency, cutoff, "highpass")


@public
def filter_bandpass(trace: Trace, sampling_frequency: int, low: int, high: int) -> Trace:
    """
    Apply a bandpass digital filter (Butterworth) to `trace`, given `sampling_frequency`, with the
    passband from `low` to `high`.

    :param trace:
    :param sampling_frequency:
    :param low:
    :param high:
    :return:
    """
    return filter_any(trace, sampling_frequency, (low, high), "bandpass")


@public
def filter_bandstop(trace: Trace, sampling_frequency: int, low: int, high: int) -> Trace:
    """
    Apply a bandstop digital filter (Butterworth) to `trace`, given `sampling_frequency`, with the
    stopband from `low` to `high`.

    :param trace:
    :param sampling_frequency:
    :param low:
    :param high:
    :return:
    """
    return filter_any(trace, sampling_frequency, (low, high), "bandstop")
