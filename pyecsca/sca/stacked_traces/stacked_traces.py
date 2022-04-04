from numba import cuda
import numpy as np
from public import public
from typing import Any, Mapping, Sequence, Tuple, Union
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
            meta = {}
        self.meta = meta
        self.samples = samples

    @classmethod
    def fromarray(cls, traces: Sequence[np.ndarray],
                  meta: Mapping[str, Any] = None) -> 'StackedTraces':
        ts = list(traces)
        min_samples = min(map(len, ts))
        for i, t in enumerate(ts):
            ts[i] = t[:min_samples]
        stacked = np.stack(ts)
        return cls(stacked, meta)

    @classmethod
    def fromtraceset(cls, traceset) -> 'StackedTraces':
        traces = [t.samples for t in traceset]
        return cls.fromarray(traces)

    def __len__(self):
        return self.samples.shape[0]

    def __getitem__(self, index):
        return self.samples[index]

    def __iter__(self):
        yield from self.samples


TPB = Union[int, Tuple[int, ...]]
CudaCTX = Tuple[
    cuda.devicearray.DeviceNDArray,
    Tuple[cuda.devicearray.DeviceNDArray, ...],
    Union[int, Tuple[int, ...]]
]


@public
class GPUTraceManager:
    @staticmethod
    def _setup1D(
        traces: StackedTraces, tpb: TPB, output_count: int
    ) -> CudaCTX:
        """
        Creates context for 1D GPU CUDA functions

        :param traces: The input stacked traces.
        :param tpb: Threads per block to invoke the kernel with.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Created context of input and output arrays and calculated
                 blocks per grid dimensions.
        """
        if not isinstance(tpb, int):
            raise TypeError("tpb is not an int")
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
    def _gpu_combine1D(
        func,
        traces: StackedTraces,
        tpb: TPB = 128,
        output_count: int = 1
    ) -> Union[CombinedTrace, Tuple[CombinedTrace, ...]]:
        """
        Runs GPU Cuda StackedTrace 1D combine function

        :param func: Function to run.
        :param traces: Stacked traces to provide as input to the function.
        :param tpb: Threads per block to invoke the kernel with
        :param output_count: Number of outputs expected from the GPU function.
        :return: Combined trace output from the GPU function
        """
        if not isinstance(tpb, int):
            raise TypeError("tpb is not an int")
        samples_global, device_outputs, bpg = GPUTraceManager._setup1D(
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
    def average(traces: StackedTraces, tpb: TPB = 128) -> CombinedTrace:
        """
        Average :paramref:`~.average.traces`, sample-wise.

        :param traces:
        :return:
        """
        return GPUTraceManager._gpu_combine1D(gpu_average, traces, tpb, 1)

    @staticmethod
    def conditional_average(traces: StackedTraces, tpb: TPB = 128) \
            -> CombinedTrace:
        """
        Not implemented due to the nature of GPU functions.

        Use sca.trace.combine.conditional_average instead.
        """
        raise NotImplementedError

    @staticmethod
    def standard_deviation(traces: StackedTraces, tpb: TPB = 128) \
            -> CombinedTrace:
        """
        Compute the sample standard-deviation of the :paramref:`~.standard_deviation.traces`, sample-wise.

        :param traces:
        :return:
        """
        return GPUTraceManager._gpu_combine1D(gpu_std_dev, traces, tpb, 1)

    @staticmethod
    def variance(traces: StackedTraces, tpb: TPB = 128) -> CombinedTrace:
        """
        Compute the sample variance of the :paramref:`~.variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        return GPUTraceManager._gpu_combine1D(gpu_variance, traces, tpb, 1)

    @staticmethod
    def average_and_variance(traces: StackedTraces, tpb: TPB = 128) \
            -> Tuple[CombinedTrace, CombinedTrace]:
        """
        Compute the average and sample variance of the :paramref:`~.average_and_variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        averages, variances = GPUTraceManager._gpu_combine1D(
            gpu_avg_var, traces, tpb, 2
        )
        return averages, variances

    @staticmethod
    def add(traces: StackedTraces, tpb: TPB = 128) -> CombinedTrace:
        """
        Add :paramref:`~.add.traces`, sample-wise.

        :param traces:
        :return:
        """
        return GPUTraceManager._gpu_combine1D(gpu_add, traces, tpb, 1)


@cuda.jit(device=True)
def _gpu_average(col: int, samples: np.ndarray, result: np.ndarray):
    """
    Cuda device thread function computing the average of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    acc = 0.
    for row in range(samples.shape[0]):
        acc += samples[row, col]
    result[col] = acc / samples.shape[0]


@cuda.jit
def gpu_average(samples: np.ndarray, result: np.ndarray):
    """
    Sample average of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result)


@cuda.jit(device=True)
def _gpu_var_from_avg(col: int, samples: np.ndarray,
                      averages: np.ndarray, result: np.ndarray):
    """
    Cuda device thread function computing the variance from the average of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param averages: Array of averages of samples.
    :param result: Result output array.
    """
    var = 0.
    for row in range(samples.shape[0]):
        current = samples[row, col] - averages[col]
        var += current * current
    result[col] = var / samples.shape[0]


@cuda.jit(device=True)
def _gpu_variance(col: int, samples: np.ndarray, result: np.ndarray):
    """
    Cuda device thread function computing the variance of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    _gpu_average(col, samples, result)
    _gpu_var_from_avg(col, samples, result, result)


@cuda.jit
def gpu_std_dev(samples: np.ndarray, result: np.ndarray):
    """
    Sample standard deviation of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)

    result[col] = sqrt(result[col])


@cuda.jit
def gpu_variance(samples: np.ndarray, result: np.ndarray):
    """
    Sample variance of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)


@cuda.jit
def gpu_avg_var(samples: np.ndarray, result_avg: np.ndarray,
                result_var: np.ndarray):
    """
    Sample average and variance of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result_avg: Result average output array.
    :param result_var: Result variance output array.
    """
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result_avg)
    _gpu_var_from_avg(col, samples, result_avg, result_var)


@cuda.jit
def gpu_add(samples: np.ndarray, result: np.ndarray):
    """
    Add samples of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)

    if col >= samples.shape[1]:
        return

    res = 0.
    for row in range(samples.shape[0]):
        res += samples[row, col]
    result[col] = res
