from numba import cuda
from numba.cuda import devicearray
import numpy as np
from public import public
from typing import Any, Mapping, Sequence, Tuple, Union, Optional
from math import sqrt

from pyecsca.sca.trace.trace import CombinedTrace


@public
class StackedTraces:
    """Samples of multiple traces and metadata"""

    meta: Mapping[str, Any]
    samples: np.ndarray

    def __init__(
            self, samples: np.ndarray,
            meta: Optional[Mapping[str, Any]] = None) -> None:
        if meta is None:
            meta = {}
        self.meta = meta
        self.samples = samples

    @classmethod
    def fromarray(cls, traces: Sequence[np.ndarray],
                  meta: Optional[Mapping[str, Any]] = None) -> 'StackedTraces':
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
    Tuple[devicearray.DeviceNDArray, ...],
    Union[int, Tuple[int, ...]]
]


@public
class GPUTraceManager:
    """Manager for operations with stacked traces on GPU"""

    traces: StackedTraces
    _tpb: TPB
    _samples_global: devicearray.DeviceNDArray

    def __init__(self, traces: StackedTraces, tpb: TPB = 128) -> None:
        if isinstance(tpb, int) and tpb % 32 != 0:
            raise ValueError('TPB should be a multiple of 32')
        if isinstance(tpb, tuple) and any(t % 32 != 0 for t in tpb):
            raise ValueError(
                'TPB should be a multiple of 32 in each dimension'
            )

        self.traces = traces
        self.tpb = tpb
        self._samples_global = cuda.to_device(self.traces.samples)

    def _setup1D(self, output_count: int) -> CudaCTX:
        """
        Creates context for 1D GPU CUDA functions

        :param traces: The input stacked traces.
        :param tpb: Threads per block to invoke the kernel with.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Created context of input and output arrays and calculated
                 blocks per grid dimensions.
        """
        if not isinstance(self.tpb, int):
            raise TypeError("tpb is not an int for a 1D kernel")

        device_output = tuple((
            cuda.device_array(self.traces.samples.shape[1])
            for _ in range(output_count)
        ))
        bpg = (self.traces.samples.size + (self.tpb - 1)) // self.tpb

        return device_output, bpg

    def _gpu_combine1D(self, func, output_count: int = 1) \
            -> Tuple[CombinedTrace, ...]:
        """
        Runs GPU Cuda StackedTrace 1D combine function

        :param func: Function to run.
        :param traces: Stacked traces to provide as input to the function.
        :param tpb: Threads per block to invoke the kernel with
        :param output_count: Number of outputs expected from the GPU function.
        :return: Combined trace output from the GPU function
        """
        device_outputs, bpg = self._setup1D(output_count)

        func[bpg, self.tpb](self._samples_global, *device_outputs)

        return tuple(
            CombinedTrace(device_output.copy_to_host(), self.traces.meta)
            for device_output
            in device_outputs
        )

    def average(self) -> CombinedTrace:
        """
        Average :paramref:`~.average.traces`, sample-wise.

        :param traces:
        :return:
        """
        return self._gpu_combine1D(gpu_average, 1)[0]

    def conditional_average(self) -> CombinedTrace:
        """
        Not implemented due to the nature of GPU functions.

        Use sca.trace.combine.conditional_average instead.
        """
        raise NotImplementedError

    def standard_deviation(self) -> CombinedTrace:
        """
        Compute the sample standard-deviation of the :paramref:`~.standard_deviation.traces`, sample-wise.

        :param traces:
        :return:
        """
        return self._gpu_combine1D(gpu_std_dev, 1)[0]

    def variance(self) -> CombinedTrace:
        """
        Compute the sample variance of the :paramref:`~.variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        return self._gpu_combine1D(gpu_variance, 1)[0]

    def average_and_variance(self) -> Tuple[CombinedTrace, CombinedTrace]:
        """
        Compute the average and sample variance of the :paramref:`~.average_and_variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        averages, variances = self._gpu_combine1D(gpu_avg_var, 2)
        return averages, variances

    def add(self) -> CombinedTrace:
        """
        Add :paramref:`~.add.traces`, sample-wise.

        :param traces:
        :return:
        """
        return self._gpu_combine1D(gpu_add, 1)[0]


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
