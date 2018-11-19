from typing import List, Callable, Tuple
from copy import copy, deepcopy
from public import public
import numpy as np
from fastdtw import fastdtw, dtw

from .process import normalize
from .trace import Trace


def align_reference(reference: Trace, *traces: Trace,
                    align_func: Callable[[Trace], Tuple[bool, int]]) -> List[Trace]:
    result = [deepcopy(reference)]
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
        result.append(Trace(copy(trace.title), copy(trace.data), result_samples))
    return result


@public
def align_correlation(reference: Trace, *traces: Trace,
                      reference_offset: int, reference_length: int,
                      max_offset: int, min_correlation: float = 0.5) -> List[Trace]:
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
        if max_correlation < min_correlation:
            return False, 0
        left_space = min(max_offset, reference_offset)
        shift = left_space + reference_length // 2
        return True, max_correlation_offset - shift

    return align_reference(reference, *traces, align_func=align_func)


@public
def align_peaks(reference: Trace, *traces: Trace,
                reference_offset: int, reference_length: int, max_offset: int) -> List[Trace]:
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
def align_sad(reference: Trace, *traces: Trace,
              reference_offset: int, reference_length: int, max_offset: int) -> List[Trace]:
    reference_part = reference.samples[reference_offset: reference_offset + reference_length]

    def align_func(trace):
        length = len(trace.samples)
        best_sad = 0
        best_offset = 0
        for offset in range(-max_offset, max_offset):
            start = reference_offset + offset
            stop = start + reference_length
            if start < 0 or stop >= length:
                continue
            trace_part = trace.samples[start:stop]
            # todo: add other distance functions here
            sad = np.sum(np.abs(reference_part - trace_part))
            if sad > best_sad:
                best_sad = sad
                best_offset = offset
        return True, best_offset
    return align_reference(reference, *traces, align_func=align_func)


@public
def align_dtw_scale(reference: Trace, *traces: Trace, radius: int = 1, fast: bool = True) -> List[Trace]:
    result = [deepcopy(reference)]
    reference_samples = reference.samples
    for trace in traces:
        if fast:
            dist, path = fastdtw(reference_samples, trace.samples, radius=radius)
        else:
            dist, path = dtw(reference_samples, trace.samples)
        result_samples = np.zeros(len(trace.samples), dtype=trace.samples.dtype)
        scale = np.ones(len(trace.samples), dtype=trace.samples.dtype)
        for x, y in path:
            result_samples[x] = trace.samples[y]
            scale[x] += 1
        result_samples //= scale
        del scale
        result.append(Trace(copy(trace.title), copy(trace.data), result_samples))
    return result


@public
def align_dtw(reference: Trace, *traces: Trace, radius: int = 1, fast: bool = True) -> List[Trace]:
    result = [deepcopy(reference)]
    reference_samples = reference.samples
    for trace in traces:
        if fast:
            dist, path = fastdtw(reference_samples, trace.samples, radius=radius)
        else:
            dist, path = dtw(reference_samples, trace.samples)
        result_samples = np.zeros(len(trace.samples), dtype=trace.samples.dtype)
        pairs = np.array(np.array(path, dtype=np.dtype("int,int")), dtype=np.dtype([("x", "int"), ("y", "int")]))
        result_samples[pairs["x"]] = trace.samples[pairs["y"]]
        del pairs
        # or manually:
        #for x, y in path:
        #    result_samples[x] = trace.samples[y]
        result.append(Trace(copy(trace.title), copy(trace.data), result_samples))
    return result
