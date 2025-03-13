"""Provides functions for matching a pattern within a trace to it."""

import numpy as np
from scipy.signal import find_peaks
from public import public
from typing import List

from pyecsca.sca.trace.process import normalize
from pyecsca.sca.trace.edit import trim
from pyecsca.sca.trace.trace import Trace


@public
def match_pattern(trace: Trace, pattern: Trace, threshold: float = 0.8) -> List[int]:
    """
    Match a :paramref:`~.match_pattern.pattern` to a :paramref:`~.match_pattern.trace`.

    Return the indices where the pattern matches, e.g. those where correlation
    of the two traces has peaks larger than :paramref:`~.match_pattern.threshold`.
    Uses the :py:func:`scipy.signal.find_peaks` function.

    :param trace: The trace to match into.
    :param pattern: The pattern to match.
    :param threshold: The threshold passed to :py:func:`scipy.signal.find_peaks` as a ``prominence`` value.
    :return: Indices where the pattern matches.
    """
    normalized = normalize(trace)
    pattern_samples = normalize(pattern).samples
    correlation = np.correlate(normalized.samples, pattern_samples, "same")
    correlation = (correlation - np.mean(correlation)) / (np.max(correlation))
    peaks, props = find_peaks(correlation, prominence=(threshold, None))
    pairs = sorted(zip(peaks, props["prominences"]), key=lambda it: it[1], reverse=True)
    half = len(pattern_samples) // 2
    filtered_peaks: List[int] = []
    for peak, _ in pairs:
        if not filtered_peaks:
            filtered_peaks.append(peak - half)
        else:
            for other_peak in filtered_peaks:
                if abs((peak - half) - other_peak) <= len(pattern_samples):
                    break
            else:
                filtered_peaks.append(peak - half)
    return filtered_peaks


@public
def match_part(
    trace: Trace, offset: int, length: int, threshold: float = 0.8
) -> List[int]:
    """
    Match a part of a :paramref:`~.match_part.trace` starting at :paramref:`~.match_part.offset` of :paramref:`~.match_part.length` to the :paramref:`~.match_part.trace`.

    Returns indices where the pattern matches, e.g. those where correlation of the two
    traces has peaks larger than :paramref:`~.match_part.threshold`.
    Uses the :py:func:`scipy.signal.find_peaks` function.

    :param trace: The trace to match into.
    :param offset: The start of the pattern in the trace to match.
    :param length: The length of the pattern in the trace to match.
    :param threshold: The threshold passed to :py:func:`scipy.signal.find_peaks` as a ``prominence`` value.
    :return: Indices where the part of the trace matches matches.
    """
    return match_pattern(trace, trim(trace, offset, offset + length), threshold)
