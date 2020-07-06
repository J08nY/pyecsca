"""
This module provides functions for aligning traces in a trace set to a reference trace within it.
"""
import numpy as np
from copy import deepcopy
from fastdtw import fastdtw, dtw
from public import public
from typing import List, Callable, Tuple

from .process import normalize
from .trace import Trace


def align_reference(reference: Trace, *traces: Trace,
                    align_func: Callable[[Trace], Tuple[bool, int]]) -> Tuple[List[Trace], List[int]]:
    result = [deepcopy(reference)]
    offsets = [0]
    for trace in traces:
        length = len(trace.samples)
        include, offset = align_func(trace)
        if not include:
            continue
        if offset == 0:
            result_samples = trace.samples.copy()
        else:
            result_samples = np.zeros(len(trace.samples), dtype=trace.samples.dtype)
            if offset > 0:
                result_samples[:length - offset] = trace.samples[offset:]
            else:
                result_samples[-offset:] = trace.samples[:length + offset]
        result.append(trace.with_samples(result_samples))
        offsets.append(offset)
    return result, offsets


@public
def align_correlation(reference: Trace, *traces: Trace,
                      reference_offset: int, reference_length: int,
                      max_offset: int, min_correlation: float = 0.5) -> Tuple[List[Trace], List[int]]:
    """
    Align `traces` to the reference `trace`. Using the cross-correlation of a part of the reference
    trace starting at `reference_offset` with `reference_length` and try to match it to a part of
    the trace being matched that is at most `max_offset` mis-aligned from the reference, pick the
    alignment offset with the largest cross-correlation. If the maximum cross-correlation of the
    trace parts being matched is below `min_correlation`, do not include the trace.

    :param reference:
    :param traces:
    :param reference_offset:
    :param reference_length:
    :param max_offset:
    :param min_correlation:
    :return:
    """
    reference_centered = normalize(reference)
    reference_part = reference_centered.samples[
                     reference_offset:reference_offset + reference_length]

    def align_func(trace):
        length = len(trace.samples)
        correlation_start = max(reference_offset - max_offset, 0)
        correlation_end = min(reference_offset + reference_length + max_offset, length - 1)
        trace_part = trace.samples[correlation_start:correlation_end]
        trace_part = (trace_part - np.mean(trace_part)) / (np.std(trace_part) * len(trace_part))
        correlation = np.correlate(trace_part, reference_part, "same")
        max_correlation_offset = correlation.argmax(axis=0)
        max_correlation = correlation[max_correlation_offset]
        del trace_part
        if max_correlation < min_correlation:
            return False, 0
        left_space = min(max_offset, reference_offset)
        shift = left_space + reference_length // 2
        return True, max_correlation_offset - shift

    return align_reference(reference, *traces, align_func=align_func)


@public
def align_peaks(reference: Trace, *traces: Trace,
                reference_offset: int, reference_length: int, max_offset: int) -> Tuple[List[Trace], List[int]]:
    """
    Align `traces` to the reference `trace` so that the maximum value within the reference trace
    window from `reference_offset` of `reference_length` aligns with the maximum
    value of the trace being aligned within `max_offset` of the reference window.

    :param reference:
    :param traces:
    :param reference_offset:
    :param reference_length:
    :param max_offset:
    :return:
    """
    reference_part = reference.samples[reference_offset: reference_offset + reference_length]
    reference_peak = np.argmax(reference_part)

    def align_func(trace):
        length = len(trace.samples)
        window_start = max(reference_offset - max_offset, 0)
        window_end = min(reference_offset + reference_length + max_offset, length - 1)
        window = trace.samples[window_start: window_end]
        window_peak = np.argmax(window)
        left_space = min(max_offset, reference_offset)
        return True, int(window_peak - reference_peak - left_space)

    return align_reference(reference, *traces, align_func=align_func)


@public
def align_offset(reference: Trace, *traces: Trace,
                 reference_offset: int, reference_length: int, max_offset: int,
                 dist_func: Callable[[np.ndarray, np.ndarray], float], max_dist: float = float("inf")) -> Tuple[List[Trace], List[int]]:
    """
    Align `traces` to the reference `trace` so that the value of the `dist_func` is minimized
    between the reference trace window from `reference_offset` of `reference_length` and the trace
    being aligned within `max_offset` of the reference window.

    :param reference:
    :param traces:
    :param reference_offset:
    :param reference_length:
    :param max_offset:
    :param dist_func:
    :return:
    """
    reference_part = reference.samples[reference_offset: reference_offset + reference_length]

    def align_func(trace):
        length = len(trace.samples)
        best_distance = 0
        best_offset = 0
        for offset in range(-max_offset, max_offset):
            start = reference_offset + offset
            stop = start + reference_length
            if start < 0 or stop >= length:
                continue
            trace_part = trace.samples[start:stop]
            distance = dist_func(reference_part, trace_part)
            if distance < best_distance:
                best_distance = distance
                best_offset = offset
        if best_distance < max_dist:
            return True, best_offset
        else:
            return False, 0
    return align_reference(reference, *traces, align_func=align_func)


@public
def align_sad(reference: Trace, *traces: Trace,
              reference_offset: int, reference_length: int, max_offset: int) -> Tuple[List[Trace], List[int]]:
    """
    Align `traces` to the reference `trace` so that the Sum Of Absolute Differences between the
    reference trace window from `reference_offset` of `reference_length` and the trace being aligned
    within `max_offset` of the reference window is maximized.

    :param reference:
    :param traces:
    :param reference_offset:
    :param reference_length:
    :param max_offset:
    :return:
    """
    def sad(reference_part, trace_part):
        return float(np.sum(np.abs(reference_part - trace_part)))

    return align_offset(reference, *traces,
                        reference_offset=reference_offset, reference_length=reference_length,
                        max_offset=max_offset, dist_func=sad)


@public
def align_dtw_scale(reference: Trace, *traces: Trace, radius: int = 1,
                    fast: bool = True) -> List[Trace]:
    """
    Align `traces` to the `reference` trace.
    Using fastdtw (Dynamic Time Warping) with scaling as per:

    Jasper G. J. van Woudenberg, Marc F. Witteman, Bram Bakker:
    Improving Differential Power Analysis by Elastic Alignment

    https://pdfs.semanticscholar.org/aceb/7c307098a414d7c384d6189226e4375cf02d.pdf

    :param reference:
    :param traces:
    :param radius:
    :param fast:
    :return:
    """
    result = [deepcopy(reference)]
    reference_samples = reference.samples
    for trace in traces:
        if fast:
            dist, path = fastdtw(reference_samples, trace.samples, radius=radius)
        else:
            dist, path = dtw(reference_samples, trace.samples)
        result_samples = np.zeros(len(reference_samples), dtype=trace.samples.dtype)
        scale = np.zeros(len(reference_samples), dtype=trace.samples.dtype)
        for x, y in path:
            result_samples[x] += trace.samples[y]
            scale[x] += 1
        result_samples /= scale
        del path
        del scale
        result.append(trace.with_samples(result_samples))
    return result


@public
def align_dtw(reference: Trace, *traces: Trace, radius: int = 1, fast: bool = True) -> List[Trace]:
    """
    Align `traces` to the `reference` trace. Using fastdtw (Dynamic Time Warping) as per:

    Stan Salvador, Philip Chan:
    FastDTW: Toward Accurate Dynamic Time Warping in Linear Time and Space

    https://cs.fit.edu/~pkc/papers/tdm04.pdf

    :param reference:
    :param traces:
    :param radius:
    :param fast:
    :return:
    """
    result = [deepcopy(reference)]
    reference_samples = reference.samples
    for trace in traces:
        if fast:
            dist, path = fastdtw(reference_samples, trace.samples, radius=radius)
        else:
            dist, path = dtw(reference_samples, trace.samples)
        result_samples = np.zeros(max((len(trace.samples), len(reference_samples))), dtype=trace.samples.dtype)
        pairs = np.array(np.array(path, dtype=np.dtype("int,int")),
                         dtype=np.dtype([("x", "int"), ("y", "int")]))
        result_samples[pairs["x"]] = trace.samples[pairs["y"]]
        del pairs
        del path
        result.append(trace.with_samples(result_samples))
    return result
