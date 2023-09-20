from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, Dict, List, TextIO, Tuple

import numpy as np
import numpy.random as npr
import numpy.typing as npt

from pyecsca.sca import (CPUTraceManager, GPUTraceManager, StackedTraces,
                         Trace, TraceSet, add, average, average_and_variance,
                         conditional_average, standard_deviation, variance)

Operation = str
Duration = int
TimeRecord = Tuple[Operation, Duration]

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


def generate_dataset(rng: npr.Generator,
                     trace_count: int,
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


def timed(time_storage: List[TimeRecord] | None = None,
          log: bool = True,
          timing_type: str = "perf_counter") \
        -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        import time
        if timing_type == "perf_counter":
            time_f = time.perf_counter_ns
        elif timing_type == "process_time":
            time_f = time.process_time_ns
        else:
            raise ValueError("Unknown timing type")

        def timed_func(*args, **kwargs) -> Callable[..., Callable]:
            start = time_f()
            result = func(*args, **kwargs)
            duration = time_f() - start

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
          timing_type: str,
          time_storage: List[TimeRecord] | None = None,
          log: bool = True) -> StackedTraces:
    time_fun = timed(time_storage, log, timing_type) if time else lambda x: x
    data = (dataset
            if from_array
            else to_traceset(dataset))
    stack_fun = stack_array if from_array else stack_traceset
    return time_fun(stack_fun)(data)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repetitions", type=int,
                        default=1, help="Number of repetitions")
    parser.add_argument(
        "-o", "--output",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Output file"
    )
    combine = parser.add_argument_group(
        "operations",
        "Operations to perform on the traces"
    )
    combine.add_argument(
        "-d", "--device",
        choices=["cpu", "gpu"],
        help="Device to use for the computation"
    )
    stacking = combine.add_mutually_exclusive_group()
    stacking.add_argument(
        "-s", "--stack",
        action="store_true",
        default=True,
        help="Use stacked traces"
    )
    stacking.add_argument(
        "--stack-traceset",
        action="store_true",
        default=False,
        help="Perform stacking from a TraceSet"
    )
    combine.add_argument(
        "--operations",
        nargs="*",
        choices=traceset_ops.keys(),
        help="Operations to perform on the traces"
    )

    chunking = parser.add_argument_group(
        "chunking",
        "Options for chunking"
    )
    chunking.add_argument(
        "-c", "--chunk",
        action="store_true",
        default=False,
        help="Use chunking for the operations",
    )
    chunking.add_argument(
        "--stream-count",
        type=int,
        default=None,
        required=False,
        help="Number of streams to use for chunking",
    )
    chunk_sizing = chunking.add_mutually_exclusive_group()
    chunk_sizing.add_argument(
        "--chunk-size",
        help="Chunk size for the operations",
        type=int,
        required=False,
        default=None
    )
    chunk_sizing.add_argument(
        "--chunk-memory-ratio",
        help="Chunk memory ratio for the operations",
        type=float,
        required=False,
        default=None
    )

    timing = parser.add_argument_group(
        "timing",
        "Options for timing"
    )
    timing.add_argument(
        "--time-stack",
        action="store_true",
        default=False,
        help="Time the stacking operation"
    )
    timing.add_argument(
        "-t", "--time",
        choices=["perf_counter", "process_time"],
        default="perf_counter",
        help="Timing function to use"
    )

    dataset = parser.add_argument_group(
        "data generation",
        "Options for data generation"
    )
    dataset.add_argument("--trace-count", type=int,
                         default=1024, help="Number of traces")
    dataset.add_argument("--trace-length", type=int,
                         default=1024, help="Number of samples per trace")
    dataset.add_argument("--seed", type=int, default=None,
                         help="Seed for the random number generator")
    dataset.add_argument(
        "--dtype",
        type=str,
        default="float32",
        choices=["float16", "float32", "float64", "int8",
                 "int16", "int32", "int64"],
        help="Data type of the samples"
    )
    dataset.add_argument(
        "--distribution",
        type=str,
        default="uniform",
        choices=["uniform", "normal"],
        help="Distribution of the samples")
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

    if args.chunk_size and args.chunk_memory_ratio:
        parser.error("Cannot specify both chunk size and chunk memory ratio")

    if args.stream_count is not None and args.stream_count <= 1:
        parser.error("Stream count must be greater than 1")

    args.chunk = (args.chunk
                  or args.stream_count is not None
                  or args.chunk_size is not None
                  or args.chunk_memory_ratio is not None)

    return args


def report(time_storage: List[TimeRecord],
           total_only: bool = False) -> None:
    if total_only:
        print(f"Total: {sum(duration for _, duration in time_storage):,} ns")
        return

    print("Timings:")
    for name, duration in time_storage:
        print(f"{name : <20} | {duration : 15,} ns")
    print("-" * 41)
    print(f"{'Total' : <20} | "
          f"{sum(duration for _, duration in time_storage) : 15,} ns")


def group_times_by_operation(time_storage: List[List[TimeRecord]]) \
        -> Dict[Operation, List[Duration]]:
    result: Dict[Operation, List[Duration]] = {}
    for times in time_storage:
        for operation, duration in times:
            if operation.startswith("stack"):
                operation = "stack"
            result.setdefault(operation, []).append(duration)

    return result


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def export_report(time_storage: List[List[TimeRecord]],
                  args: argparse.Namespace,
                  output: TextIO) -> None:
    by_operation = group_times_by_operation(time_storage)
    data: Dict[str, Any] = {}
    data["config"] = {
        "repetitions": args.repetitions,
        "operations": {
            "device": args.device,
            "operations": args.operations,
            "stack": args.stack,
            "stack_traceset": args.stack_traceset,
            "time_function": args.time,
        },
        "dataset": {
            "seed": args.seed,
            "trace_count": args.trace_count,
            "trace_length": args.trace_length,
            "data_type": args.dtype,
            "distribution": args.distribution,
            "low": args.low,
            "high": args.high,
            "mean": args.mean,
            "std_dev": args.std,
        }
    }
    data["timing"] = [
        {
            "repetition": rep_num + 1,
            "timings": {
                ("stack"
                 if name.startswith("stack")
                 else name): duration
                for name, duration
                in rep
            }
        }
        for rep_num, rep
        in enumerate(time_storage)
    ]
    data["timing"].append({
        "repetition": "total",
        "timings": {
            name: sum(durations)
            for name, durations
            in by_operation.items()
        },
    })
    data["timing"][-1]["total"] = sum(
        duration
        for duration
        in data["timing"][-1]["timings"].values()
    )

    operations = []
    if args.time_stack:
        operations.append("stack")
    operations.extend(args.operations)

    data["summary"] = {
        op: {
            "sum": np.sum(by_operation[op]),
            "average": np.mean(by_operation[op]),
            "min": np.min(by_operation[op]),
            "max": np.max(by_operation[op]),
            "std_dev": np.std(by_operation[op]),
            "variance": np.var(by_operation[op]),
            "median": np.median(by_operation[op]),
            "q25": np.quantile(by_operation[op], 0.25),
            "q75": np.quantile(by_operation[op], 0.75),
        }
        for op in operations
    }

    json.dump(data,
              output,
              cls=NumpyEncoder,
              indent=4)
    output.write("\n")


def repetition(args: argparse.Namespace,
               rng: npr.Generator) -> List[TimeRecord]:
    # Prepare time storage
    time_storage: List[TimeRecord] | None = []

    # Generate data
    if args.verbose:
        print("Generating data...")
    dataset = generate_dataset(rng,
                               args.trace_count,
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
                     args.time,
                     time_storage,
                     args.verbose)
    else:
        data = to_traceset(dataset)

    if not args.operations:
        report(time_storage)
        return time_storage

    if args.verbose:
        print("Performing operations...")

    # Operations on stacked traces
    if args.stack:
        # Initialize trace manager
        assert isinstance(data, StackedTraces)
        trace_manager = (CPUTraceManager(data)
                         if args.device == "cpu"
                         else GPUTraceManager(
                             data,
                             chunk=args.chunk,
                             chunk_size=args.chunk_size,
                             chunk_memory_ratio=args.chunk_memory_ratio,
                             stream_count=args.stream_count))

        # Perform operations
        for op in args.operations:
            if args.verbose:
                print(f"Performing {op}...")
            op_func = getattr(trace_manager, op)
            timed(time_storage, args.verbose, args.time)(op_func)()
    else:
        assert isinstance(data, TraceSet)

        # Perform operations
        for op in args.operations:
            if args.verbose:
                print(f"Performing {op}...")
            op_func = traceset_ops[op]
            timed(time_storage, args.verbose, args.time)(op_func)(*data)

    if args.verbose:
        print("------------------------")
    report(time_storage)
    print("-" * 41 + "\n")
    return time_storage


def main(args: argparse.Namespace) -> None:
    if args.verbose:
        print(f"Repetitions: {args.repetitions}")
        print(f"Dataset: {args.trace_count} x {args.trace_length} "
              "(count x length)")
        print(f"Device: {args.device},",
              "stacked" if args.stack else "not stacked")
        print(f"Operations: {', '.join(args.operations)}")

    time_storage: List[List[TimeRecord]] = []
    rng = np.random.default_rng(args.seed)
    for i in range(args.repetitions):
        print(f"Repetition {i + 1} of {args.repetitions}")
        time_storage.append(repetition(args, rng))

    total_time = sum(sum(dur for _, dur in rep)
                     for rep in time_storage)
    print("\nSummary")
    print(f"Total: {total_time:,} ns")
    export_report(time_storage, args, args.output)


if __name__ == "__main__":
    args = _get_args(_get_parser())
    main(args)
