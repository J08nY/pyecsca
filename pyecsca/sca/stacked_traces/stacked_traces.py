from numba import cuda
import numpy as np
from public import public
from typing import Any, Mapping, MutableSequence, Tuple, Union
from math import sqrt

from pyecsca.sca.trace.trace import CombinedTrace


@public
class StackedTraces:
    """Samples of multiple traces and metadata"""

    meta: Mapping[str, Any]
    samples: np.ndarray

    def __init__(
            self, samples: np.ndarray,
            meta: Mapping[str, Any] = None) -> None:
        if meta is None:
            meta = dict()
        self.meta = meta
        self.samples = samples

    @classmethod
    def fromarray(cls, traces: MutableSequence[np.ndarray],
                  meta: Mapping[str, Any] = None) -> 'StackedTraces':
        min_samples = min(map(len, traces))
        for i, t in enumerate(traces):
            traces[i] = t[:min_samples]
        stacked = np.stack(traces)
        return cls(stacked, meta)

    @classmethod
    def fromtraceset(cls, traceset) -> 'StackedTraces':
        traces = [t.samples for t in traceset]
        return cls.fromarray(traces)

    def __len__(self):
        return self.traces.shape[0]

    def __getitem__(self, index):
        return self.traces

    def __iter__(self):
        yield from self.traces


@public
class GPUTraceManager:
    TPB = Union[int, Tuple[int, ...]]
    BPG = Union[int, Tuple[int, ...]]
    Samples = cuda.devicearray.DeviceNDArray
    Output = cuda.devicearray.DeviceNDArray
    CudaCTX = Tuple[Samples, Tuple[Output, ...], BPG]

    @staticmethod
    def setup(traces: StackedTraces, tpb: int, output_count: int) -> CudaCTX:
        if tpb % 32 != 0:
            raise ValueError('Threads per block should be a multiple of 32')

        samples = traces.samples
        samples_global = cuda.to_device(samples)
        device_output = tuple((
            cuda.device_array(samples.shape[1])
            for _ in range(output_count)
        ))
        bpg = (samples.size + (tpb - 1)) // tpb

        return samples_global, device_output, bpg

    @staticmethod
    def _gpu_combine(func, traces: StackedTraces,
                     tpb: int = 128,
                     output_count: int = 1) \
            -> Union[CombinedTrace, Tuple[CombinedTrace, ...]]:
        samples_global, device_outputs, bpg = GPUTraceManager.setup(
            traces, tpb, output_count
        )

        func[bpg, tpb](samples_global, *device_outputs)

        if len(device_outputs) == 1:
            return CombinedTrace(
                device_outputs[0].copy_to_host(),
                traces.meta
            )
        return (
            CombinedTrace(device_output.copy_to_host(), traces.meta)
            for device_output
            in device_outputs
        )

    @staticmethod
    def average(traces: StackedTraces, tpb: int = 128) -> CombinedTrace:
        return GPUTraceManager._gpu_combine(gpu_average, traces, tpb, 1)

    @staticmethod
    def conditional_average(traces: StackedTraces, tpb: int = 128) \
            -> CombinedTrace:
        raise NotImplementedError

    @staticmethod
    def standard_deviation(traces: StackedTraces, tpb: int = 128) \
            -> CombinedTrace:
        return GPUTraceManager._gpu_combine(gpu_std_dev, traces, tpb, 1)

    @staticmethod
    def variance(traces: StackedTraces, tpb: int = 128) -> CombinedTrace:
        return GPUTraceManager._gpu_combine(gpu_variance, traces, tpb, 1)

    @staticmethod
    def average_and_variance(traces: StackedTraces, tpb: int = 128) \
            -> Tuple[CombinedTrace, CombinedTrace]:
        return GPUTraceManager._gpu_combine(gpu_avg_var, traces, tpb, 2)

    @staticmethod
    def add(traces: StackedTraces, tpb: int = 128) -> CombinedTrace:
        return GPUTraceManager._gpu_combine(gpu_add, traces, tpb, 1)


@cuda.jit(device=True)
def _gpu_average(col: int, samples: np.ndarray, result: np.ndarray):
    acc = 0.
    for row in range(samples.shape[0]):
        acc += samples[row, col]
    result[col] = acc / samples.shape[0]


@cuda.jit
def gpu_average(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result)


@cuda.jit(device=True)
def _gpu_var_from_avg(col: int, samples: np.ndarray,
                      averages: np.ndarray, result: np.ndarray):
    var = 0.
    for row in range(samples.shape[0]):
        current = samples[row, col] - averages[col]
        var += current * current
    result[col] = var / samples.shape[0]


@cuda.jit(device=True)
def _gpu_variance(col: int, samples: np.ndarray, result: np.ndarray):
    _gpu_average(col, samples, result)
    _gpu_var_from_avg(col, samples, result, result)


@cuda.jit
def gpu_std_dev(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)

    result[col] = sqrt(result[col])


@cuda.jit
def gpu_variance(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)


@cuda.jit
def gpu_avg_var(samples: np.ndarray, result_avg: np.ndarray,
                result_var: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result_avg)
    _gpu_var_from_avg(col, samples, result_avg, result_var)


@cuda.jit
def gpu_add(samples: np.ndarray, result: np.ndarray):
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    res = 0.
    for row in range(samples.shape[0]):
        res += samples[row, col]
    result[col] = res


@cuda.jit
def gpu_subtract(samples_one: np.ndarray, samples_other: np.ndarray,
                 result: np.ndarray):
    raise NotImplementedError
