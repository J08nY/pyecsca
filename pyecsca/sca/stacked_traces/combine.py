from __future__ import annotations

from numba import cuda
from numba.cuda import devicearray
import numpy as np
import numpy.typing as npt
from math import sqrt

from public import public
from typing import Callable, Union, Tuple, Optional, cast, List

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

    def conditional_average(self,
                            cond: Callable[[npt.NDArray[np.number]], bool]) \
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


CHUNK_MEMORY_RATIO = 0.4


@public
class GPUTraceManager(BaseTraceManager):
    """Manager for operations with stacked traces on GPU"""

    _tpb: TPB
    _chunk_size: Optional[int]

    def __init__(self,
                 traces: StackedTraces,
                 tpb: TPB = 128,
                 chunk: bool = False,
                 chunk_size: Optional[int] = None,
                 chunk_memory_ratio: Optional[float] = None) -> None:
        if not cuda.is_available():
            raise RuntimeError("CUDA is not available, "
                               "use CPUTraceManager instead")

        if chunk_size and chunk_memory_ratio:
            raise ValueError("Only one of chunk_size and chunk_memory_ratio "
                             "can be specified")

        if chunk_memory_ratio is not None \
           and (chunk_memory_ratio <= 0 or chunk_memory_ratio > 0.5):
            raise ValueError("Chunk memory ratio should be in (0, 0.5], "
                             "because two chunks are stored in memory "
                             "at once")

        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("Chunk size should be positive")
        
        chunk = (chunk
                 or chunk_size is not None
                 or chunk_memory_ratio is not None)

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
        # If chunking is used, the samples are stored in Fortran order
        # for contiguous memory access
        if chunk:
            self._traces.samples = np.asfortranarray(self._traces.samples)

        self._tpb = tpb
        if not chunk:
            self._combine_func = self._gpu_combine1D_all
            self._chunk_size = None
        else:
            self._combine_func = self._gpu_combine1D_chunked
            if chunk_size is not None:
                self._chunk_size = chunk_size
            else:
                self._chunk_size = self.chunk_size_from_ratio(
                    chunk_memory_ratio
                    if chunk_memory_ratio is not None
                    else CHUNK_MEMORY_RATIO,
                    self._traces.samples.itemsize)

    @staticmethod
    def chunk_size_from_ratio(chunk_memory_ratio: float,
                              item_size: int) -> int:
        mem_size = cuda.current_context().get_memory_info().free
        return int(
            chunk_memory_ratio * mem_size / item_size)

    def _gpu_combine1D(self, func, output_count: int = 1) \
            -> Union[CombinedTrace, List[CombinedTrace]]:
        results = self._combine_func(func, output_count)

        if output_count == 1:
            return CombinedTrace(
                results[0],
                self._traces.meta
            )

        return [
            CombinedTrace(result, self._traces.meta)
            for result
            in results
        ]

    def _gpu_combine1D_all(self, func, output_count: int = 1) \
            -> List[npt.NDArray[np.number]]:
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
        device_outputs = [
            cuda.device_array(self._traces.samples.shape[1])
            for _ in range(output_count)
        ]

        bpg = (self._traces.samples.shape[1] + self._tpb - 1) // self._tpb
        func[bpg, self._tpb](device_input, *device_outputs)
        return [device_output.copy_to_host()
                for device_output in device_outputs]

    def _gpu_combine1D_chunked(self, func, output_count: int = 1) \
            -> List[npt.NDArray[np.number]]:
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

        chunk_results: List[List[npt.NDArray[np.number]]] = [
            list()
            for _ in range(output_count)]

        for chunk in range(chunk_count):
            start = chunk * self._chunk_size
            end = min((chunk + 1) * self._chunk_size,
                      self._traces.samples.shape[1])

            device_input = cuda.to_device(
                self._traces.samples[:, start:end],
                stream=data_stream
            )
            device_outputs = [cuda.device_array(
                end - start, stream=data_stream) for _ in range(output_count)]

            bpg = (end - start + self._tpb - 1) // self._tpb
            func[bpg, self._tpb, compute_stream](
                device_input, *device_outputs
            )

            compute_stream.synchronize()
            for output_i, device_output in enumerate(device_outputs):
                chunk_results[output_i].append(
                    device_output.copy_to_host(stream=data_stream))

        data_stream.synchronize()

        return [np.concatenate(chunk_result)
                for chunk_result in chunk_results]

    def average(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_average, 1))

    def conditional_average(self,
                            cond: Callable[[npt.NDArray[np.number]], bool]) \
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
def _gpu_average(col: int, samples: npt.NDArray[np.number],
                 result: npt.NDArray[np.number]):
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
def gpu_average(samples: npt.NDArray[np.number],
                result: npt.NDArray[np.number]):
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
def _gpu_var_from_avg(col: int, samples: npt.NDArray[np.number],
                      averages: npt.NDArray[np.number],
                      result: npt.NDArray[np.number]):
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
def _gpu_variance(col: int, samples: npt.NDArray[np.number],
                  result: npt.NDArray[np.number]):
    """
    Cuda device thread function computing the variance of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    _gpu_average(col, samples, result)
    _gpu_var_from_avg(col, samples, result, result)


@cuda.jit(cache=True)
def gpu_std_dev(samples: npt.NDArray[np.number],
                result: npt.NDArray[np.number]):
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
def gpu_variance(samples: npt.NDArray[np.number],
                 result: npt.NDArray[np.number]):
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
def gpu_avg_var(samples: npt.NDArray[np.number],
                result_avg: npt.NDArray[np.number],
                result_var: npt.NDArray[np.number]):
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
def gpu_add(samples: npt.NDArray[np.number],
            result: npt.NDArray[np.number]):
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

    def conditional_average(self,
                            condition: Callable[[npt.NDArray[np.number]],
                                                bool]) \
            -> CombinedTrace:
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
