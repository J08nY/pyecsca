from __future__ import annotations

from numba import cuda
from numba.cuda import devicearray
import numpy as np
from math import sqrt

from public import public
from typing import Callable, Union, Tuple, Optional, cast

from pyecsca.sca.trace.trace import CombinedTrace
from pyecsca.sca.stacked_traces import StackedTraces

TPB = Union[int, Tuple[int, ...]]
CudaCTX = Tuple[devicearray.DeviceNDArray, ...]


@public
class BaseTraceManager:
    """Base class for trace managers"""

    _traces: StackedTraces

    def __init__(self, traces: StackedTraces) -> None:
        self._traces = traces

    def average(self) -> CombinedTrace:
        """
        Average :paramref:`~.average.traces`, sample-wise.

        :param traces:
        :return:
        """
        raise NotImplementedError

    def conditional_average(self, cond: Callable[[np.ndarray], bool]) \
            -> CombinedTrace:
        """
        Average :paramref:`~.conditional_average.traces` for which the
        :paramref:`~.conditional_average.condition` is ``True``, sample-wise.

        :param traces:
        :param condition:
        :return:
        """
        raise NotImplementedError

    def standard_deviation(self) -> CombinedTrace:
        """
        Compute the sample standard-deviation of the
        :paramref:`~.standard_deviation.traces`, sample-wise.

        :param traces:
        :return:
        """
        raise NotImplementedError

    def variance(self) -> CombinedTrace:
        """
        Compute the sample variance of the
        :paramref:`~.variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        raise NotImplementedError

    def average_and_variance(self) -> Tuple[CombinedTrace, CombinedTrace]:
        """
        Compute the sample average and variance of the
        :paramref:`~.average_and_variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        raise NotImplementedError

    def add(self) -> CombinedTrace:
        """
        Add :paramref:`~.add.traces`, sample-wise.

        :param traces:
        :return:
        """
        raise NotImplementedError


@public
class GPUTraceManager(BaseTraceManager):
    """Manager for operations with stacked traces on GPU"""

    _tpb: TPB
    _chunk_size: Optional[int]

    def __init__(self,
                 traces: StackedTraces,
                 tpb: TPB = 128,
                 chunk_size: Optional[int] = None) -> None:
        if not cuda.is_available():
            raise RuntimeError("CUDA is not available, "
                               "use CPUTraceManager instead")
        dev = cuda.get_current_device()
        warp_size = dev.WARP_SIZE
        max_tpb = dev.MAX_THREADS_PER_BLOCK
        if isinstance(tpb, int):
            if tpb % warp_size != 0:
                raise ValueError(
                    f'TPB should be a multiple of WARP_SIZE ({warp_size})'
                )
            if tpb > max_tpb:
                raise ValueError(
                    'TPB should be smaller than '
                    'MAX_THREADS_PER_BLOCK ({max_tpb})'
                )
        if isinstance(tpb, tuple) and any(
            t > max_tpb or t % warp_size != 0 for t in tpb
        ):
            raise ValueError(
                f'TPB should be a multiple of WARP_SIZE ({warp_size}) '
                f'and smaller than MAX_THREADS_PER_BLOCK ({max_tpb})'
                'in each dimension'
            )

        super().__init__(traces)
        self._traces.samples = np.asfortranarray(self._traces.samples)

        self._tpb = tpb
        self._chunk_size = chunk_size
        self._combine_func = self._gpu_combine1D_all if chunk_size is None \
            else self._gpu_combine1D_chunked

    def _setup1D(self, output_count: int) -> CudaCTX:
        """
        Creates context for 1D GPU CUDA functions

        :param traces: The input stacked traces.
        :param tpb: Threads per block to invoke the kernel with.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Created context of input and output arrays and calculated
                 blocks per grid dimensions.
        """
        if not isinstance(self._tpb, int):
            raise TypeError("tpb is not an int for a 1D kernel")

        device_output = tuple((
            cuda.device_array(self._traces.samples.shape[1])
            for _ in range(output_count)
        ))

        return device_output

    def _gpu_combine1D(self, func, output_count: int = 1) \
            -> Union[CombinedTrace, Tuple[CombinedTrace, ...]]:
        device_outputs = self._setup1D(output_count)

        self._combine_func(func, device_outputs)

        if len(device_outputs) == 1:
            return CombinedTrace(
                device_outputs[0].copy_to_host(),
                self._traces.meta
            )
        return tuple(
            CombinedTrace(device_output.copy_to_host(), self._traces.meta)
            for device_output
            in device_outputs
        )

    def _gpu_combine1D_all(self, func, device_outputs: CudaCTX) -> None:
        """
        Runs a combination function on the samples column-wise.

        All samples are processed at once.
        :param func: Function to run.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Combined trace output from the GPU function
        """
        assert self._chunk_size is None
        assert isinstance(self._tpb, int)

        device_input = cuda.to_device(self._traces.samples)

        bpg = (self._traces.samples.shape[1] + self._tpb - 1) // self._tpb
        func[bpg, self._tpb](device_input, *device_outputs)

    def _gpu_combine1D_chunked(self, func, device_outputs: CudaCTX) -> None:
        """
        Runs a combination function on the samples column-wise.

        The samples are processed in chunks.
        :param func: Function to run.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Combined trace output from the GPU function
        """
        assert self._chunk_size is not None
        assert isinstance(self._tpb, int)

        chunk_count = (
            self._traces.samples.shape[1] + self._chunk_size - 1
        ) // self._chunk_size

        data_stream = cuda.stream()
        compute_stream = cuda.stream()

        for chunk in range(chunk_count):
            start = chunk * self._chunk_size
            end = min((chunk + 1) * self._chunk_size,
                      self._traces.samples.shape[1])

            device_input = cuda.to_device(
                self._traces.samples[:, start:end],
                stream=data_stream
            )

            bpg = (end - start + self._tpb - 1) // self._tpb
            func[bpg, self._tpb, compute_stream](
                device_input, *device_outputs
            )

            device_input.copy_to_host(stream=data_stream)

        data_stream.synchronize()
        compute_stream.synchronize()

    def average(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_average, 1))

    def conditional_average(self, cond: Callable[[np.ndarray], bool]) \
            -> CombinedTrace:
        raise NotImplementedError()

    def standard_deviation(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_std_dev, 1))

    def variance(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_variance, 1))

    def average_and_variance(self) -> Tuple[CombinedTrace, CombinedTrace]:
        averages, variances = self._gpu_combine1D(gpu_avg_var, 2)
        return averages, variances

    def add(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_add, 1))


@cuda.jit(device=True, cache=True)
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


@cuda.jit(cache=True)
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


@cuda.jit(device=True, cache=True)
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


@cuda.jit(device=True, cache=True)
def _gpu_variance(col: int, samples: np.ndarray, result: np.ndarray):
    """
    Cuda device thread function computing the variance of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    _gpu_average(col, samples, result)
    _gpu_var_from_avg(col, samples, result, result)


@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
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


@cuda.jit(cache=True)
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


@public
class CPUTraceManager:
    """Manager for operations on stacked traces on CPU."""

    traces: StackedTraces

    def __init__(self, traces: StackedTraces) -> None:
        self.traces = traces

    def average(self) -> CombinedTrace:
        """
        Compute the average of the :paramref:`~.average.traces`, sample-wise.

        :param traces:
        :return:
        """
        return CombinedTrace(
            np.average(self.traces.samples, 0),
            self.traces.meta
        )

    def conditional_average(self, condition: Callable[[np.ndarray], bool]) -> CombinedTrace:
        """
        Compute the conditional average of the :paramref:`~.conditional_average.traces`, sample-wise.

        :param traces:
        :return:
        """
        # TODO: Consider other ways to implement this
        samples = self.traces.samples
        mask = samples[np.apply_along_axis(condition, 1, samples)]
        return CombinedTrace(
            np.average(samples[mask], 1),
            self.traces.meta
        )

    def standard_deviation(self) -> CombinedTrace:
        """
        Compute the sample standard-deviation of the :paramref:`~.standard_deviation.traces`, sample-wise.

        :param traces:
        :return:
        """
        return CombinedTrace(
            np.std(self.traces.samples, 0),
            self.traces.meta
        )

    def variance(self) -> CombinedTrace:
        """
        Compute the sample variance of the :paramref:`~.variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        return CombinedTrace(
            np.var(self.traces.samples, 0),
            self.traces.meta
        )

    def average_and_variance(self) -> Tuple[CombinedTrace, CombinedTrace]:
        """
        Compute the average and sample variance of the :paramref:`~.average_and_variance.traces`, sample-wise.

        :param traces:
        :return:
        """
        return (
            self.average(),
            self.variance()
        )

    def add(self) -> CombinedTrace:
        """
        Add :paramref:`~.add.traces`, sample-wise.

        :param traces:
        :return:
        """
        return CombinedTrace(
            np.sum(self.traces.samples, 0),
            self.traces.meta
        )
