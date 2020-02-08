"""
This module provides functions for matching a pattern within a trace to it.
"""
import numpy as np
from scipy.signal import find_peaks
from public import public
from typing import List

from .process import normalize
from .edit import trim
from .trace import Trace


@public
def match_pattern(trace: Trace, pattern: Trace, threshold: float = 0.8) -> List[int]:
    normalized = normalize(trace)
    pattern_samples = normalize(pattern).samples
    correlation = np.correlate(normalized.samples, pattern_samples, "same")
    correlation = (correlation - np.mean(correlation)) / (np.max(correlation))
    peaks, props = find_peaks(correlation, prominence=(threshold, None))
    pairs = sorted(zip(peaks, props["prominences"]), key=lambda it: it[1], reverse=True)
    half = len(pattern_samples) // 2
    filtered_peaks: List[int] = []
    for peak, prominence in pairs:
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
def match_part(trace: Trace, offset: int, length: int) -> List[int]:
    return match_pattern(trace, trim(trace, offset, offset + length))
