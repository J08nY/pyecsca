from __future__ import annotations

import argparse
from typing import Any, Callable

import numpy as np
import numpy.random as npr
import numpy.typing as npt

from pyecsca.sca import (CPUTraceManager, GPUTraceManager, StackedTraces,
                         Trace, TraceSet, add, average, average_and_variance,
                         conditional_average, standard_deviation, variance)

traceset_ops = {
    "average": average,
    "conditional_average": conditional_average,
    "standard_deviation": standard_deviation,
    "variance": variance,
    "average_and_variance": average_and_variance,
    "add": add,
}


def _generate_floating(rng: npr.Generator,
                       trace_count: int,
                       trace_length: int,
                       dtype: npt.DTypeLike = np.float32,
                       distribution: str = "uniform",
                       low: float = 0.0,
                       high: float = 1.0,
                       mean: float = 0.0,
                       std: float = 0.0) -> np.ndarray:
    if not np.issubdtype(dtype, np.floating):
        raise ValueError("dtype must be a floating point type")

    dtype_ = (dtype if (np.issubdtype(dtype, np.float32)
                        or np.issubdtype(dtype, np.float64))
              else np.float32)
    if distribution == "uniform":
        samples = rng.random((trace_count, trace_length),
                             dtype=dtype_)  # type: ignore

        if (not np.issubdtype(dtype, np.float32)
                and not np.issubdtype(dtype, np.float64)):
            samples = samples.astype(dtype)
        return (samples * (high - low) + low)
    elif distribution == "normal":
        return (rng
                .normal(mean, std, (trace_count, trace_length))
                .clip(low, high)
                .astype(dtype))

    raise ValueError("Unknown distribution")


def _generate_integers(rng: npr.Generator,
                       trace_count: int,
                       trace_length: int,
                       dtype: npt.DTypeLike = np.int32,
                       distribution: str = "uniform",
                       low: int = 0,
                       high: int = 1,
                       mean: float = 0.0,
                       std: float = 0.0) -> np.ndarray:
    if not np.issubdtype(dtype, np.integer):
        raise ValueError("dtype must be an integer type")

    if distribution == "uniform":
        return rng.integers(low,
                            high,
                            size=(trace_count, trace_length),
                            dtype=dtype)  # type: ignore
    elif distribution == "normal":
        return (rng
                .normal(mean, std, (trace_count, trace_length))
                .astype(dtype)
                .clip(low, high - 1))

    raise ValueError("Unknown distribution")


def generate_dataset(trace_count: int,
                     trace_length: int,
                     dtype: npt.DTypeLike = np.float32,
                     distribution: str = "uniform",
                     low: float | int = 0,
                     high: float | int = 1,
                     mean: float | int = 0,
                     std: float | int = 1,
                     seed: int | None = None) -> np.ndarray:
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
                      distribution,
                      cast_fun(low),  # type: ignore
                      cast_fun(high),  # type: ignore
                      mean,
                      std)

    return samples


def timed(time_storage: list[tuple[str, int]] | None = None,
          log: bool = True) \
        -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        import time

        def timed_func(*args, **kwargs) -> Callable[..., Callable]:
            start = time.perf_counter_ns()
            result = func(*args, **kwargs)
            duration = time.perf_counter_ns() - start
            if log:
                print(f"{func.__name__} took {duration} ns")
            if time_storage is not None:
                time_storage.append((func.__name__, duration))
            return result
        return timed_func
    return decorator


def stack_traceset(traceset: TraceSet) -> StackedTraces:
    return StackedTraces.fromtraceset(traceset)


def stack_array(dataset: np.ndarray) -> StackedTraces:
    return StackedTraces.fromarray(dataset)  # type: ignore


def to_traceset(dataset: np.ndarray) -> TraceSet:
    return TraceSet(*(Trace(samples) for samples in dataset))


def stack(dataset: np.ndarray,
          from_array: bool,
          time: bool,
          time_storage: list[tuple[str, int]] | None = None,
          log: bool = True) -> StackedTraces:
    time_fun = timed(time_storage, log) if time else lambda x: x
    data = (dataset
            if from_array
            else to_traceset(dataset))
    stack_fun = stack_array if from_array else stack_traceset
    return time_fun(stack_fun)(data)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    combine = parser.add_argument_group(
        "operations",
        "Operations to perform on the traces"
    )
    combine.add_argument(
        "-d", "--device",
        choices=["cpu", "gpu"],
    )
    stacking = combine.add_mutually_exclusive_group()
    stacking.add_argument(
        "-s", "--stack",
        action="store_true",
        default=False
    )
    stacking.add_argument(
        "--stack-traceset",
        action="store_true",
        default=False
    )
    combine.add_argument(
        "--time-stack",
        action="store_true",
        default=False
    )

    combine.add_argument(
        "--operations",
        nargs="*",
        choices=["average", "conditional_average", "standard_deviation",
                 "variance", "average_and_variance", "add"],
    )

    dataset = parser.add_argument_group(
        "data generation",
        "Options for data generation"
    )
    dataset.add_argument("--trace-count", type=int, default=1000)
    dataset.add_argument("--trace-length", type=int, default=1000)
    dataset.add_argument("--seed", type=int, default=None)
    dataset.add_argument(
        "--dtype",
        type=str,
        default="float32",
        choices=["float16", "float32", "float64", "int8",
                 "int16", "int32", "int64"],
    )
    dataset.add_argument(
        "--distribution",
        type=str,
        default="uniform",
        choices=["uniform", "normal"])
    dataset.add_argument("--low", type=float, default=0.0,
                         help="Inclusive lower bound for generated samples")
    dataset.add_argument("--high", type=float, default=1.0,
                         help="Exclusive upper bound for generated samples")
    dataset.add_argument("--mean", type=float, default=0.0,
                         help="Mean of the normal distribution")
    dataset.add_argument("--std", type=float, default=1.0,
                         help="Standard deviation of the normal distribution")

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true")
    verbosity.add_argument("-q", "--quiet", action="store_true")
    return parser


def _get_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    args = parser.parse_args()

    if args.time_stack and not args.stack and not args.stack_traceset:
        parser.error("Cannot time stack without stacking")

    if not args.operations and not args.stack:
        parser.error("No operation specified")

    if args.low >= args.high:
        parser.error("Lower bound must be smaller than upper bound")

    if args.operations and not args.device:
        parser.error("Device must be specified when performing operations")

    if (args.operations
            and args.device == "gpu"
            and not args.stack
            and not args.stack_traceset):
        args.stack = True
        args.stack_traceset = False

    return args


def report(time_storage: list[tuple[str, int]]) -> None:
    print("Timings:")
    for name, duration in time_storage:
        print(f"{name : <20} | {duration : 15,} ns")
    print("-" * 41)
    print(f"{'Total' : <20} | "
          f"{sum(duration for _, duration in time_storage) : 15,} ns")


def main(args: argparse.Namespace) -> None:
    if args.verbose:
        print(f"Dataset: {args.trace_count} x {args.trace_length} "
              "(count x length)")
        print(f"Device: {args.device},",
              "stacked" if args.stack else "not stacked")
        print(f"Operations: {', '.join(args.operations)}")

    # Prepare time storage
    time_storage: list[tuple[str, int]] | None = []

    # Generate data
    if args.verbose:
        print("Generating data...")
    dataset = generate_dataset(args.trace_count,
                               args.trace_length,
                               args.dtype,
                               args.distribution,
                               args.low,
                               args.high,
                               args.mean,
                               args.std,
                               args.seed)

    # Transform data for operations input
    if args.stack:
        if args.verbose:
            print("Stacking data...")
        data = stack(dataset,
                     not args.stack_traceset,
                     args.time_stack,
                     time_storage,
                     args.verbose)
    else:
        data = to_traceset(dataset)

    if not args.operations:
        report(time_storage)
        return

    if args.verbose:
        print("Performing operations...")

    # Operations on stacked traces
    if args.stack:
        # Initialize trace manager
        assert isinstance(data, StackedTraces)
        tm_class = (CPUTraceManager
                    if args.device == "cpu"
                    else GPUTraceManager)

        trace_manager = tm_class(data)

        # Perform operations
        for op in args.operations:
            if args.verbose:
                print(f"Performing {op}...")
            op_func = getattr(trace_manager, op)
            timed(time_storage, args.verbose)(op_func)()
    else:
        assert isinstance(data, TraceSet)

        # Perform operations
        for op in args.operations:
            if args.verbose:
                print(f"Performing {op}...")
            op_func = traceset_ops[op]
            timed(time_storage, args.verbose)(op_func)(*data)

    if args.verbose:
        print("------------------------")
    report(time_storage)


if __name__ == "__main__":
    args = _get_args(_get_parser())
    main(args)
