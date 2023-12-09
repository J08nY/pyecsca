from __future__ import annotations

from argparse import Namespace, FileType, ArgumentParser
from contextlib import contextmanager, nullcontext
from itertools import product
from pathlib import Path
from copy import copy
from csv import DictWriter
import json
import sys
from typing import (Any, Callable, Dict, List, Optional, TextIO,
                    Tuple, Union, cast)
from warnings import warn

import numpy as np
import numpy.random as npr
import numpy.typing as npt

from pyecsca.sca import (CPUTraceManager, GPUTraceManager, StackedTraces,
                         Trace, TraceSet, add, average, average_and_variance,
                         conditional_average, standard_deviation, variance)

Operation = str
Duration = int
TimeRecord = Tuple[Operation, Duration]

TRACESET_OPS = {
    "average": average,
    "conditional_average": conditional_average,
    "standard_deviation": standard_deviation,
    "variance": variance,
    "average_and_variance": average_and_variance,
    "add": add,
    "pearson_corr": None,
}

OPERATIONS = list(TRACESET_OPS.keys())
DTYPES = ["float32", "float16", "float64", "int8", "int16", "int32", "int64"]
TIMING_TYPES = ["perf_counter", "process_time"]
DISTRIBUTIONS = ["uniform", "normal"]
DEVICES = ["cpu", "gpu"]


def _generate_floating(rng: npr.Generator,
                       shape: tuple[int, ...],
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
        samples = rng.random(shape,
                             dtype=dtype_)  # type: ignore

        if (not np.issubdtype(dtype, np.float32)
                and not np.issubdtype(dtype, np.float64)):
            samples = samples.astype(dtype)
        return (samples * (high - low) + low)
    elif distribution == "normal":
        return (rng
                .normal(mean, std, shape)
                .clip(low, high)
                .astype(dtype))

    raise ValueError("Unknown distribution")


def _generate_integers(rng: npr.Generator,
                       shape: tuple[int, ...],
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
                            size=shape,
                            dtype=dtype)  # type: ignore
    elif distribution == "normal":
        return (rng
                .normal(mean, std, shape)
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
                     std: float | int = 1) -> np.ndarray:
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

    shape = (trace_count, trace_length) if trace_length > 1 else (trace_count,)
    gen_fun, cast_fun = ((_generate_integers, int)
                         if np.issubdtype(dtype, np.integer) else
                         (_generate_floating, float))
    samples = gen_fun(rng,
                      shape,
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
          time: bool = False,
          timing_type: str | None = None,
          time_storage: List[TimeRecord] | None = None,
          log: bool = True) -> StackedTraces:
    if timing_type is None:
        timing_type = "perf_counter"
    if time and time_storage is None:
        time_storage = []
    time_fun = timed(time_storage, log, timing_type) if time else lambda x: x
    data = (dataset
            if from_array
            else to_traceset(dataset))
    stack_fun = stack_array if from_array else stack_traceset
    return time_fun(stack_fun)(data)


def _get_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "-r", "--repetitions",
        type=int,
        default=1,
        help="Number of repetitions"
    )
    parser.add_argument(
        "-p", "--param-file",
        type=FileType("r"),
        default=None,
        help=("Parameters file - JSON file containing an object or array "
              "of objects with keys corresponding to the arguments "
              "of this script and values being either a single value "
              "or a list of values to be used for the parameters. In case "
              "of a list, all combinations of the values are used. "
              "\"repetitions\", \"seed\" and \"operations\" are left as-is.")
    )

    output = parser.add_argument_group(
        "Output",
        "Options for output"
    )
    output.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (no --param-file) or directory (--param-file)"
    )
    output.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format"
    )
    output.add_argument(
        "--report-total",
        action="store_true",
        default=False,
        help="Add total times to the report (only for --format json)"
    )
    output.add_argument(
        "--report-summary",
        action="store_true",
        default=False,
        help="Add summary to the report (only for --format json)"
    )
    output.add_argument(
        "--aggregate",
        action="store_true",
        default=True,
        help="Aggregate results from all parameter combinations "
             "(only with --param-file and --format csv)",
    )
    output.add_argument(
        "--aggregate-only",
        action="store_true",
        default=False,
        help="Aggregate results from all parameter combinations "
             "(only with --param-file and --format csv)",
    )

    combine = parser.add_argument_group(
        "Operations",
        "Operations to perform on the traces"
    )
    combine.add_argument(
        "-d", "--device",
        choices=DEVICES,
        help="Device to use for the computation"
    )
    stacking = combine.add_mutually_exclusive_group()
    stacking.add_argument(
        "-s", "--stack",
        action="store_true",
        default=True,
        help="Use stacked traces (necessary for --device gpu, default: True)"
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
        choices=OPERATIONS,
        help="Operations to perform on the traces"
    )

    chunking = parser.add_argument_group(
        "Chunking",
        "Options for chunking (only for --device gpu)"
    )
    chunking.add_argument(
        "-c", "--chunk",
        action="store_true",
        default=False,
        help=("Use chunking for the operations "
              "(set automatically if other chunking arguments are set)"),
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
        "Timing",
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
        choices=TIMING_TYPES,
        default=TIMING_TYPES[0],
        help="Timing function to use",
    )

    dataset = parser.add_argument_group(
        "Data generation",
        "Options for data generation"
    )
    dataset.add_argument(
        "--trace-count",
        type=int,
        default=None,
        help="Number of traces"
    )
    dataset.add_argument(
        "--trace-length",
        type=int,
        default=None,
        help="Number of samples per trace"
    )
    dataset.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for the random number generator"
    )
    dataset.add_argument(
        "--dtype",
        type=str,
        default=DTYPES[0],
        choices=DTYPES,
        help="Data type of the samples"
    )
    dataset.add_argument(
        "--distribution",
        type=str,
        default=DISTRIBUTIONS[0],
        choices=DISTRIBUTIONS,
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


ParamValueScalar = Union[int, float, str, bool, list[str]]
ParamValueMixed = Union[ParamValueScalar,
                        list[int], list[float], list[str], list[bool]]
SCALAR_PARAMS = {
    "repetitions": int,
    "seed": int,
    "operations": OPERATIONS,
}
LIST_PARAMS = {
    "device": DEVICES,
    "stack": bool,
    "stack_traceset": bool,
    "chunk": bool,
    "stream_count": int,
    "chunk_size": int,
    "chunk_memory_ratio": float,
    "time_stack": bool,
    "time": TIMING_TYPES,
    "n_trace_count": int,
    "e_trace_count": int,
    "n_trace_length": int,
    "e_trace_length": int,
    "n_n_samples": int,
    "e_n_samples": int,
    "dtype": DTYPES,
    "distribution": DISTRIBUTIONS,
    "low": float,
    "high": float,
    "mean": float,
    "std": float,
}


def _check_args(args: Namespace) -> Optional[str]:
    if args.time_stack and not args.stack and not args.stack_traceset:
        return "Cannot time stack without stacking"

    if not args.operations and not args.stack:
        return "No operation specified"

    if args.low >= args.high:
        return "Lower bound must be smaller than upper bound"

    if args.operations and not args.device:
        return "Device must be specified when performing operations"

    if args.chunk_size and args.chunk_memory_ratio:
        return "Cannot specify both chunk size and chunk memory ratio"

    if args.stream_count is not None and args.stream_count <= 1:
        return "Stream count must be greater than 1"

    return None


def _postprocess_args(args: Namespace) -> None:
    if (args.operations
            and args.device == "gpu"
            and not args.stack
            and not args.stack_traceset):
        args.stack = True
        args.stack_traceset = False

    args.chunk = (args.chunk
                  or args.stream_count is not None
                  or args.chunk_size is not None
                  or args.chunk_memory_ratio is not None)

    if args.aggregate_only:
        args.aggregate = True

    if args.param_file is not None:
        args.trace_count, args.trace_length = get_dimensions(**vars(args))

        outdir: Optional[Path] = args.output
        assert outdir is not None
        filename = params_filename(**args.__dict__)
        args.output = outdir / filename


def generate_params_combinations(params: Dict[str, ParamValueMixed]) \
        -> List[Dict[str, ParamValueScalar]]:
    # Items of dict retain order since Python 3.7
    scalar_params = cast(Dict[str, ParamValueScalar],
                         {k: v
                          for k, v
                          in params.items()
                          if k in SCALAR_PARAMS})
    comb_keys = [k for k in params.keys() if k in LIST_PARAMS]
    comb_values = [
        v if isinstance(v, list) else [v]
        for k, v in params.items()
        if k in LIST_PARAMS
    ]

    return [
        scalar_params | dict(zip(comb_keys, comb))
        for comb
        in product(*comb_values)
    ]


def _check_dimensions_params(n_trace_count: Optional[int] = None,
                             e_trace_count: Optional[int] = None,
                             n_trace_length: Optional[int] = None,
                             e_trace_length: Optional[int] = None,
                             n_n_samples: Optional[int] = None,
                             e_n_samples: Optional[int] = None) -> None:
    count_ok = 2 == sum(
        1 if x is not None else 0
        for x
        in (e_trace_count, n_trace_count,
            e_trace_length, n_trace_length,
            e_n_samples, n_n_samples)
    )
    if not count_ok:
        raise ValueError(
            "Exactly two of dimensions' parameters must be specified")

    pairs_ok = not (
        (n_trace_count is not None and e_trace_count is not None)
        or (n_trace_length is not None and e_trace_length is not None)
        or (n_n_samples is not None and e_n_samples is not None)
    )
    if not pairs_ok:
        raise ValueError(
            "At most one of each dimension's parameters must be specified")

    positive_ok = all(
        x is None or x > 0
        for x
        in (n_trace_count, e_trace_count, n_trace_length, e_trace_length,
            n_n_samples, e_n_samples)
    )
    if not positive_ok:
        raise ValueError(
            "All dimensions' parameters must be positive")


def get_dimensions(n_trace_count: Optional[int] = None,
                   e_trace_count: Optional[int] = None,
                   n_trace_length: Optional[int] = None,
                   e_trace_length: Optional[int] = None,
                   n_n_samples: Optional[int] = None,
                   e_n_samples: Optional[int] = None,
                   **kwargs) -> Tuple[int, int]:
    _check_dimensions_params(n_trace_count, e_trace_count,
                             n_trace_length, e_trace_length,
                             n_n_samples, e_n_samples)

    if e_trace_count is not None:
        n_trace_count = 2 ** e_trace_count
    if e_trace_length is not None:
        n_trace_length = 2 ** e_trace_length
    if e_n_samples is not None:
        n_n_samples = 2 ** e_n_samples

    if n_n_samples is None:
        assert n_trace_count is not None and n_trace_length is not None
        return n_trace_count, n_trace_length

    if n_trace_count is None:
        assert n_trace_length is not None
        if n_n_samples % n_trace_length != 0 or n_n_samples < n_trace_length:
            raise ValueError(
                "Number of samples must be divisible by "
                "and greater than trace length")
        n_trace_count = n_n_samples // n_trace_length
        return n_trace_count, n_trace_length

    if n_n_samples % n_trace_count != 0 or n_n_samples < n_trace_count:
        raise ValueError(
            "Number of samples must be divisible by "
            "and greater than trace count")
    n_trace_length = n_n_samples // n_trace_count
    return n_trace_count, n_trace_length


def params_filename(device: str,
                    dtype: str,
                    distribution: str,
                    time: str,
                    format: str,
                    trace_count: Optional[int] = None,
                    trace_length: Optional[int] = None,
                    **params) -> str:
    timing = ''.join(map(lambda x: x[0], time.split('_')))
    dtype = dtype[0] + dtype[-2:]
    distrib = distribution[:4]

    if trace_count is None or trace_length is None:
        trace_count, trace_length = get_dimensions(**params)
    dims = f"{trace_count}x{trace_length}"

    return f"{device}_{timing}_{dtype}_{distrib}_{dims}.{format}"


def parse_params_dict(params: dict[str, ParamValueMixed],
                      base_args: Namespace) -> tuple[list[Namespace],
                                                     Optional[str]]:
    params_combs = generate_params_combinations(params)
    args_list: list[Namespace] = []
    error: Optional[str] = None
    for p in params_combs:
        args = copy(base_args)
        for k, v in p.items():
            setattr(args, k, v)

        cur_error = _check_args(args)
        if cur_error is not None:
            error = cur_error

        _postprocess_args(args)
        args_list.append(args)
    return args_list, error


def load_params_file(file: TextIO,
                     base_args: Namespace) -> tuple[list[Namespace],
                                                    Optional[str]]:
    with file:
        params = json.load(file)

    if isinstance(params, dict):
        params = [params]

    args_list = []
    error = None
    for p in params:
        if not isinstance(p, dict):
            raise ValueError("Parameters must be a dictionary")
        cur_args_list, cur_error = parse_params_dict(p, base_args)
        if not cur_args_list and cur_error is not None:
            error = cur_error
        args_list.extend(cur_args_list)

    return args_list, error


def _check_output(output: Optional[Path],
                  param_file: Optional[TextIO]) -> None:

    # Single output file
    if param_file is None:
        if output is None or not output.exists() or output.is_file():
            return
        raise ValueError("Output must be a file")

    # Output directory
    if output is None:
        raise ValueError(
            "Output must be specified when using a parameter file"
        )

    if output.exists() and not output.is_dir():
        raise ValueError("Output must be a directory")


def _get_args(parser: ArgumentParser) -> list[Namespace]:
    args = parser.parse_args()

    output: Optional[Path] = args.output
    _check_output(output, args.param_file)

    # Single run, command line arguments
    if args.param_file is None:
        error = _check_args(args)
        if error is not None:
            parser.error(error)
        return [args]

    # Multiple runs, parameter file and command line arguments
    assert output is not None
    output.mkdir(parents=True, exist_ok=True)

    args_list, error = load_params_file(args.param_file, args)
    if not args_list:
        if error is None:
            parser.error("No parameters found")
        parser.error(error)

    return args_list


def print_times(time_storage: List[TimeRecord],
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


@contextmanager
def default_open(path: Optional[Path], mode: str = "r"):
    if path is None:
        yield sys.stdout
    else:
        with path.open(mode) as f:
            yield f


def _report_json_single(time_storage: List[List[TimeRecord]],
                        args: Namespace) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    data["config"] = {
        "repetitions": args.repetitions,
        "operations": {
            "device": args.device,
            "operations": args.operations,
            "stack": args.stack,
            "stack_traceset": args.stack_traceset,
            "time": args.time,
        },
        "dataset": {
            "seed": args.seed,
            "trace_count": args.trace_count,
            "trace_length": args.trace_length,
            "dtype": args.dtype,
            "distribution": args.distribution,
            "low": args.low,
            "high": args.high,
            "mean": args.mean,
            "std": args.std,
        }
    }
    data["timing"] = [
        {
            "repetition": rep_num,
            "durations": {
                ("stack"
                 if name.startswith("stack")
                 else name): duration
                for name, duration
                in rep
            }
        }
        for rep_num, rep
        in enumerate(time_storage, start=1)
    ]

    by_operation: Dict[Operation, List[Duration]] = {}
    if args.report_total or args.report_summary:
        by_operation = group_times_by_operation(time_storage)

    if args.report_total:
        data["timing"].append({
            "repetition": "total",
            "durations": {
                name: sum(durations)
                for name, durations
                in by_operation.items()
            },
        })
        data["timing"][-1]["total"] = sum(
            duration
            for duration
            in data["timing"][-1]["durations"].values()
        )

    if args.report_summary:
        operations = (["stack"] if args.time_stack else []) + args.operations
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

    return data


def _export_report_json(time_storage: List[tuple[Namespace,
                                           List[List[TimeRecord]]]],
                        aggregate: bool,
                        aggregate_only: bool) -> None:
    reports = list(map(lambda x: (x[0], _report_json_single(x[1], x[0])),
                       time_storage))

    if not aggregate_only:
        for args, report in reports:
            with default_open(args.output, "w") as outfile:
                json.dump(report, outfile)

    if aggregate:
        args, _ = time_storage[0]
        output: Path = args.output
        aggr_path = output.parent / "all.json"

        with aggr_path.open("w") as outfile:
            json.dump([r for _, r in reports], outfile)
        return


_CSV_BASE_FIELDS = [
    "device",
    "stack",
    "stack_traceset",
    "chunk",
    "stream_count",
    "chunk_size",
    "chunk_memory_ratio",
    "time",
    "trace_count",
    "trace_length",
    "seed",
    "dtype",
    "distribution",
    "low",
    "high",
    "mean",
    "std",
]
_CSV_ALL_FIELDS = _CSV_BASE_FIELDS + ["repetition", "operation", "duration"]


def _report_csv_base(args: Namespace) -> Dict[str, Any]:
    return {k: getattr(args, k) for k in _CSV_BASE_FIELDS}


def _export_report_csv_single(time_storage: List[List[TimeRecord]],
                              args: Namespace,
                              current_writer: Optional[DictWriter[str]],
                              aggr_writer: Optional[DictWriter[str]]):
    data = _report_csv_base(args)
    for repnum, rep in enumerate(time_storage, start=1):
        # Saves time by not copying and just always rewriting
        # these 3 fields
        data["repetition"] = repnum
        for operation, duration in rep:
            data["operation"] = operation
            data["duration"] = duration
            if aggr_writer is not None:
                aggr_writer.writerow(data)
            if current_writer is not None:
                current_writer.writerow(data)


@contextmanager
def conditional_dictwriter(condition: bool,
                           path: Optional[Path],
                           mode: str = "r",
                           *args,
                           **kwargs):
    cm = default_open(path, mode) if condition else nullcontext()
    with cm as f:
        if f is None:
            yield None
        else:
            writer = DictWriter(f, *args, **kwargs)
            writer.writeheader()
            yield writer


def _export_report_csv(time_storage: List[tuple[Namespace,
                                          List[List[TimeRecord]]]],
                       aggregate: bool,
                       aggregate_only: bool) -> None:
    args, _ = time_storage[0]
    output: Path = args.output
    aggr_path = output.parent / "all.csv"
    aggr_cm = conditional_dictwriter(aggregate,
                                     aggr_path,
                                     "w",
                                     _CSV_ALL_FIELDS,
                                     extrasaction="ignore",
                                     dialect="unix",
                                     delimiter=";")
    with aggr_cm as aggr_writer:
        for args, times in time_storage:
            current_cm = conditional_dictwriter(not aggregate_only,
                                                args.output,
                                                "w",
                                                _CSV_ALL_FIELDS,
                                                extrasaction="ignore",
                                                dialect="unix",
                                                delimiter=";")
            with current_cm as current_writer:
                _export_report_csv_single(times,
                                          args,
                                          current_writer,
                                          aggr_writer)


def export_report(args_durations: List[tuple[Namespace,
                                             List[List[TimeRecord]]]],
                  export_format: str,
                  **kwargs) -> None:
    if export_format == "json":
        _export_report_json(args_durations, **kwargs)
    elif export_format == "csv":
        _export_report_csv(args_durations, **kwargs)
    else:
        raise ValueError(f"Unknown export format {export_format}")


def repetition(args: Namespace,
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
                               args.std)

    # Transform data for operations input
    if not args.stack:
        data = to_traceset(dataset)
    else:
        if args.verbose:
            print("Stacking data...")
        data = stack(dataset,
                     not args.stack_traceset,
                     args.time_stack,
                     args.time,
                     time_storage,
                     args.verbose)

    if not args.operations:
        print_times(time_storage)
        return time_storage

    if args.verbose:
        print("Performing operations...")

    if args.stack:
        # Operations on stacked traces
        assert isinstance(data, StackedTraces)
        # Initialize trace manager
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
            op_func = getattr(trace_manager, op, None)
            if op_func is None:
                warn(f"Unknown operation {op}")
                continue
            inputs = ()
            if op == "pearson_corr":
                inputs = (generate_dataset(rng,
                                           args.trace_count,
                                           1,
                                           args.dtype,
                                           args.distribution,
                                           args.low,
                                           args.high,
                                           args.mean,
                                           args.std),)
            timed(time_storage, args.verbose, args.time)(op_func)(*inputs)
    else:
        assert isinstance(data, TraceSet)
        # Perform operations
        for op in args.operations:
            if args.verbose:
                print(f"Performing {op}...")
            op_func = TRACESET_OPS.get(op)
            if op_func is None:
                warn(f"Unknown operation {op}")
                continue
            timed(time_storage, args.verbose, args.time)(op_func)(*data)

    if args.verbose:
        print("------------------------")
    print_times(time_storage)
    print("-" * 41 + "\n")
    return time_storage


def main(args: Namespace) -> List[List[TimeRecord]]:
    if args.verbose:
        print("Arguments:")
        print('\n'.join(f"\t{k}: {v}" for k, v in vars(args).items()))

    time_storage: List[List[TimeRecord]] = []
    rng = np.random.default_rng(args.seed)
    for i in range(args.repetitions):
        print(f"Repetition {i + 1} of {args.repetitions}")
        time_storage.append(repetition(args, rng))

    total_time = sum(sum(dur for _, dur in rep)
                     for rep in time_storage)
    print("\nSummary")
    print(f"Total: {total_time:,} ns")
    # export_report(time_storage, args, args.output)
    return time_storage


if __name__ == "__main__":
    args_list = _get_args(_get_parser())
    assert args_list
    results = []
    try:
        for args in args_list:
            results.append(main(args))
    finally:
        common_args = args_list[0]
        export_report(list(zip(args_list, results)),
                      common_args.format,
                      aggregate=common_args.aggregate,
                      aggregate_only=common_args.aggregate_only)
