from __future__ import annotations
import numpy as np
import numpy.random as npr
import numpy.typing as npt

from pyecsca.sca import (
    Trace,
    StackedTraces,
    GPUTraceManager,
    CPUTraceManager,
    TraceSet,
    CombinedTrace
)


def _generate_floating(rng: npr.Generator,
                       trace_count: int,
                       trace_length: int,
                       dtype: npt.DTypeLike = np.float32,
                       low: float = 0.0,
                       high: float = 1.0) -> np.ndarray:
    if not np.issubdtype(dtype, np.floating):
        raise ValueError("dtype must be a floating point type")

    dtype_ = (dtype if (np.issubdtype(dtype, np.float32)
                        or np.issubdtype(dtype, np.float64))
              else np.float32)
    samples = rng.random((trace_count, trace_length),
                         dtype=dtype_)  # type: ignore

    if (not np.issubdtype(dtype, np.float32)
            and not np.issubdtype(dtype, np.float64)):
        samples = samples.astype(dtype)
    return (samples * (high - low) + low)


def _generate_integers(rng: npr.Generator,
                       trace_count: int,
                       trace_length: int,
                       dtype: npt.DTypeLike = np.int32,
                       low: int = 0,
                       high: int = 1) -> np.ndarray:
    if not np.issubdtype(dtype, np.integer):
        raise ValueError("dtype must be an integer type")

    return rng.integers(low,
                        high,
                        size=(trace_count, trace_length),
                        dtype=dtype)  # type: ignore


def generate_traceset(trace_count: int,
                      trace_length: int,
                      dtype: npt.DTypeLike = np.float32,
                      low: float | int = 0,
                      high: float | int = 1,
                      seed: int | None = None) -> TraceSet:
    """Generate a TraceSet with random samples

    For float dtype only float32 and float64 are supported natively,
    other floats are converted after generation.
    For int dtype, all numpy int types are supported.
    :param trace_count: Number of traces
    :param trace_length: Number of samples per trace
    :param dtype: Data type of the samples
    :param low: Lower bound of the samples
    :param high: Upper bound of the samples
    :param seed: Seed for the random number generator
    :return: TraceSet
    """
    if (not np.issubdtype(dtype, np.integer)
            and not np.issubdtype(dtype, np.floating)):
        raise ValueError("dtype must be an integer or floating point type")

    rng = np.random.default_rng(seed)
    gen_fun, cast_fun = ((_generate_integers, int)
                         if np.issubdtype(dtype, np.integer) else
                         (_generate_floating, float))
    samples = gen_fun(rng,
                      trace_count,
                      trace_length,
                      dtype,
                      cast_fun(low),  # type: ignore
                      cast_fun(high))  # type: ignore

    return TraceSet(*(Trace(t) for t in samples))
