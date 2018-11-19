from copy import copy
from typing import Union, Tuple, Any
from public import public
import numpy as np

from .trace import Trace


@public
def trim(trace: Trace, start: int = None, end: int = None) -> Trace:
    if start is None:
        start = 0
    if end is None:
        end = len(trace.samples)
    if start > end:
        raise ValueError("Invalid trim arguments.")
    return Trace(copy(trace.title), copy(trace.data), trace.samples[start:end].copy())


@public
def reverse(trace: Trace) -> Trace:
    return Trace(copy(trace.title), copy(trace.data), np.flipud(trace.samples))


@public
def pad(trace: Trace, lengths: Union[Tuple[int, int], int], values: Union[Tuple[Any, Any], Any] = (0, 0)) -> Trace:
    if not isinstance(lengths, tuple):
        lengths = (lengths, lengths)
    if not isinstance(values, tuple):
        values = (values, values)
    return Trace(copy(trace.title), copy(trace.data), np.pad(trace.samples, lengths, "constant", constant_values=values))
