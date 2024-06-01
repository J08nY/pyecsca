"""Provides functions for editing traces as if they were tapes you can trim, reverse, etc."""
import numpy as np
from public import public
from typing import Union, Tuple, Any, Optional

from pyecsca.sca.trace.trace import Trace


@public
def trim(trace: Trace, start: Optional[int] = None, end: Optional[int] = None) -> Trace:
    """
    Trim the `trace` samples, output contains samples between the `start` and `end` indices.

    :param trace: The trace to trim.
    :param start: Starting index (inclusive).
    :param end: Ending index (exclusive).
    :return:
    """
    if start is None:
        start = 0
    if end is None:
        end = len(trace.samples)
    if start > end:
        raise ValueError("Invalid trim arguments.")
    return trace.with_samples(trace.samples[start:end].copy())


@public
def reverse(trace: Trace) -> Trace:
    """
    Reverse the samples of the `trace`.

    :param trace: The trace to reverse.
    :return:
    """
    return trace.with_samples(np.flipud(trace.samples).copy())


@public
def pad(
    trace: Trace,
    lengths: Union[Tuple[int, int], int],
    values: Union[Tuple[Any, Any], Any] = (0, 0),
) -> Trace:
    """
    Pad the samples of the `trace` by `values` at the beginning and end.

    :param trace: The trace to pad.
    :param lengths: How much to pad at the beginning and end, either symmetric (if integer) or asymmetric (if tuple).
    :param values: What value to pad with, either symmetric or asymmetric (if tuple).
    :return:
    """
    if not isinstance(lengths, tuple):
        lengths = (lengths, lengths)
    if not isinstance(values, tuple):
        values = (values, values)
    return trace.with_samples(
        np.pad(trace.samples, lengths, "constant", constant_values=values)
    )


@public
def stretch(trace: Trace, length: int) -> Trace:
    """
    Stretch (or squeeze) a trace linearly to fit a given length.

    :param trace: The trace to stretch (or squeeze).
    :param length: The length it should be.
    :return:
    """
    current_indices = np.arange(len(trace))
    target_indices = np.linspace(0, len(trace) - 1, length)
    return trace.with_samples(np.interp(target_indices, current_indices, trace.samples))
