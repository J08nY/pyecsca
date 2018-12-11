import numpy as np
from copy import copy
from public import public
from typing import Union, Tuple, Any

from .trace import Trace


@public
def trim(trace: Trace, start: int = None, end: int = None) -> Trace:
    """
    Trim the `trace` samples, output contains samples between the `start` and `end` indices.

    :param trace:
    :param start:
    :param end:
    :return:
    """
    if start is None:
        start = 0
    if end is None:
        end = len(trace.samples)
    if start > end:
        raise ValueError("Invalid trim arguments.")
    return Trace(copy(trace.title), copy(trace.data), trace.samples[start:end].copy())


@public
def reverse(trace: Trace) -> Trace:
    """
    Reverse the samples of the `trace`.

    :param trace:
    :return:
    """
    return Trace(copy(trace.title), copy(trace.data), np.flipud(trace.samples))


@public
def pad(trace: Trace, lengths: Union[Tuple[int, int], int],
        values: Union[Tuple[Any, Any], Any] = (0, 0)) -> Trace:
    """
    Pad the samples of the `trace` by `values` at the beginning and end.

    :param trace:
    :param lengths: How much to pad at the beginning and end, either symmetric (if integer) or asymmetric (if tuple).
    :param values: What value to pad with,  either symmetric or asymmetric (if tuple).
    :return:
    """
    if not isinstance(lengths, tuple):
        lengths = (lengths, lengths)
    if not isinstance(values, tuple):
        values = (values, values)
    return Trace(copy(trace.title), copy(trace.data),
                 np.pad(trace.samples, lengths, "constant", constant_values=values))
