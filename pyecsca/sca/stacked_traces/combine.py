from abc import ABC, abstractmethod

from numba import cuda
from numba.cuda import devicearray
from numba.cuda.cudadrv.devicearray import DeviceNDArray
import numpy as np
import numpy.typing as npt
from math import sqrt

from numba.cuda.types import CUDADispatcher
from public import public
from typing import Callable, Union, Tuple, Optional, cast, List

from pyecsca.sca.trace.trace import CombinedTrace
from pyecsca.sca.stacked_traces import StackedTraces

TPB = Union[int, Tuple[int, ...]]
CudaCTX = Tuple[devicearray.DeviceNDArray, ...]


@public
class BaseTraceManager(ABC):
    """Base class for trace managers"""

    _traces: StackedTraces

    def __init__(self, traces: StackedTraces) -> None:
        self._traces = traces

    @abstractmethod
    def average(self) -> CombinedTrace:
        """
        Average traces, sample-wise.

        :return: The average of the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def conditional_average(
        self, cond: Callable[[npt.NDArray[np.number]], bool]
    ) -> CombinedTrace:
        """
        Average traces for which the
        :paramref:`~.conditional_average.cond` is ``True``, sample-wise.

        :param cond: The condition for selecting the traces.
        :return: The average of (some of) the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def standard_deviation(self) -> CombinedTrace:
        """
        Compute the sample standard-deviation of the traces, sample-wise.

        :return: The standard deviation of the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def variance(self) -> CombinedTrace:
        """
        Compute the sample variance of the traces, sample-wise.

        :return: The variance of the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def average_and_variance(self) -> List[CombinedTrace]:
        """
        Compute the sample average and variance of the traces, sample-wise.

        :return: The average and variance of the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def add(self) -> CombinedTrace:
        """
        Add traces, sample-wise.

        :return: The sum of the traces.
        """
        raise NotImplementedError

    @abstractmethod
    def pearson_corr(
        self, intermediate_values: npt.NDArray[np.number]
    ) -> CombinedTrace:
        """
        Calculates the Pearson correlation coefficient between the given samples and intermediate values sample-wise.

        :param intermediate_values: A 1D array of shape (n,) containing the intermediate values.
        :type intermediate_values: npt.NDArray[np.number]
        :return: The Pearson correlation coefficient between the samples and intermediate values.
        """
        raise NotImplementedError


InputType = Union[npt.NDArray[np.number], npt.ArrayLike]


CHUNK_MEMORY_RATIO = 0.4
STREAM_COUNT = 4


@public
class GPUTraceManager(BaseTraceManager):  # pragma: no cover
    """Manager for operations with stacked traces on GPU"""

    _tpb: TPB
    _chunk_size: Optional[int]
    _stream_count: Optional[int]

    def __init__(
        self,
        traces: StackedTraces,
        tpb: TPB = 128,
        chunk: bool = False,
        chunk_size: Optional[int] = None,
        chunk_memory_ratio: Optional[float] = None,
        stream_count: Optional[int] = None,
    ) -> None:
        """
        :param traces: Stacked traces on which to operate.
        :param tpb: Threads per block to use for GPU operations.
        :param chunk: Whether to chunk the traces.
        :param chunk_size: Number of samples to use for chunking.
                           Chunks will be `chunk_size` x `trace_count`.
        :param chunk_memory_ratio: Part of available memory to use for chunking.
        :param stream_count: Number of streams to use for chunking.
        """
        self._check_init_args(chunk_size, chunk_memory_ratio, tpb)

        chunk = (
            chunk
            or stream_count is not None
            or chunk_size is not None
            or chunk_memory_ratio is not None
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
            self._stream_count = None
        else:
            self._combine_func = self._gpu_combine1D_chunked
            self._stream_count = (
                stream_count if stream_count is not None else STREAM_COUNT
            )
            if chunk_size is not None:
                self._chunk_size = chunk_size
            else:
                self._chunk_size = self.chunk_size_from_ratio(
                    (
                        chunk_memory_ratio
                        if chunk_memory_ratio is not None
                        else CHUNK_MEMORY_RATIO
                    ),
                    item_size=self._traces.samples.itemsize,
                    chunk_item_count=self._traces.samples.shape[0],
                )

    @staticmethod
    def _check_tpb(tpb: TPB) -> None:
        dev = cuda.get_current_device()
        warp_size = dev.WARP_SIZE
        max_tpb = dev.MAX_THREADS_PER_BLOCK
        if isinstance(tpb, int):
            if tpb % warp_size != 0:
                raise ValueError(f"TPB should be a multiple of WARP_SIZE ({warp_size})")
            if tpb > max_tpb:
                raise ValueError(
                    "TPB should be smaller than " "MAX_THREADS_PER_BLOCK ({max_tpb})"
                )
        if isinstance(tpb, tuple) and any(
            t > max_tpb or t % warp_size != 0 for t in tpb
        ):
            raise ValueError(
                f"TPB should be a multiple of WARP_SIZE ({warp_size}) "
                f"and smaller than MAX_THREADS_PER_BLOCK ({max_tpb})"
                "in each dimension"
            )

    @staticmethod
    def _check_chunk_sizing(
        chunk_size: Optional[int], chunk_memory_ratio: Optional[float]
    ) -> None:
        if chunk_size and chunk_memory_ratio:
            raise ValueError(
                "Only one of chunk_size and chunk_memory_ratio " "can be specified"
            )

        if chunk_memory_ratio is not None and (
            chunk_memory_ratio <= 0 or chunk_memory_ratio > 0.5
        ):
            raise ValueError(
                "Chunk memory ratio should be in (0, 0.5], "
                "because two chunks are stored in memory "
                "at once"
            )

        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("Chunk size should be positive")

    @staticmethod
    def _check_init_args(
        chunk_size: Optional[int], chunk_memory_ratio: Optional[float], tpb: TPB
    ) -> None:
        if not cuda.is_available():
            raise RuntimeError("CUDA is not available, " "use CPUTraceManager instead")

        GPUTraceManager._check_chunk_sizing(chunk_size, chunk_memory_ratio)
        GPUTraceManager._check_tpb(tpb)

    @staticmethod
    def chunk_size_from_ratio(
        chunk_memory_ratio: float,
        element_size: Optional[int] = None,
        item_size: Optional[int] = None,
        chunk_item_count: Optional[int] = None,
    ) -> int:
        if (element_size is None) == (item_size is None and chunk_item_count is None):
            raise ValueError(
                "Either element_size or item_size and chunk_item_count "
                "should be specified"
            )
        if element_size is None:
            assert item_size is not None
            assert chunk_item_count is not None
            element_size = item_size * chunk_item_count

        mem_size = cuda.current_context().get_memory_info().free
        return int(chunk_memory_ratio * mem_size / element_size)

    @property
    def traces_shape(self) -> Tuple[int, ...]:
        return self._traces.samples.shape

    def _gpu_combine1D(
        self,
        func: CUDADispatcher,
        inputs: Optional[List[InputType]] = None,
        output_count: int = 1,
    ) -> Union[CombinedTrace, List[CombinedTrace]]:
        inputs = [] if inputs is None else inputs
        results = self._combine_func(func, inputs, output_count)

        if output_count == 1:
            return CombinedTrace(results[0], self._traces.meta)

        return [CombinedTrace(result, self._traces.meta) for result in results]

    def _gpu_combine1D_all(
        self, func: CUDADispatcher, inputs: List[InputType], output_count: int = 1
    ) -> List[npt.NDArray[np.number]]:
        """
        Runs a combination function on the samples column-wise.

        All samples are processed at once.
        :param func: Function to run.
        :param output_count: Number of outputs expected from the GPU function.
        :return: Combined trace output from the GPU function
        """
        if not isinstance(self._tpb, int):
            raise ValueError("Something went wrong. " "TPB should be an int")

        samples_input = cuda.to_device(self._traces.samples)
        device_inputs = [cuda.to_device(inp) for inp in inputs]  # type: ignore
        device_outputs = [
            cuda.device_array(self._traces.samples.shape[1])
            for _ in range(output_count)
        ]

        bpg = (self._traces.samples.shape[1] + self._tpb - 1) // self._tpb
        func[bpg, self._tpb](samples_input, *device_inputs, *device_outputs)
        return [device_output.copy_to_host() for device_output in device_outputs]

    def _gpu_combine1D_chunked(
        self, func: CUDADispatcher, inputs: List[InputType], output_count: int = 1
    ) -> List[npt.NDArray[np.number]]:
        if self._chunk_size is None:
            raise ValueError("Something went wrong. " "Chunk size should be specified")
        if self._stream_count is None:
            raise ValueError(
                "Something went wrong. " "Stream count should be specified"
            )
        if not isinstance(self._tpb, int):
            raise ValueError("Something went wrong. " "TPB should be an int")

        chunk_count = (
            self._traces.samples.shape[1] + self._chunk_size - 1
        ) // self._chunk_size
        streams = [cuda.stream() for _ in range(self._stream_count)]
        events: List[Union[None, cuda.Event]] = [
            None for _ in range(self._stream_count)
        ]

        # Pre-allocate pinned memory for each stream
        pinned_input_buffers = [
            cuda.pinned_array(
                (self._traces.samples.shape[0], self._chunk_size),
                dtype=self._traces.samples.dtype,
                order="F",
            )
            for _ in range(self._stream_count)
        ]

        device_inputs = [cuda.to_device(inp) for inp in inputs]  # type: ignore

        chunk_results: List[List[npt.NDArray[np.number]]] = [
            [] for _ in range(output_count)
        ]

        with cuda.defer_cleanup():
            for chunk in range(chunk_count):
                start = chunk * self._chunk_size
                end = min((chunk + 1) * self._chunk_size, self._traces.samples.shape[1])
                stream = streams[chunk % self._stream_count]
                event = events[chunk % self._stream_count]
                if event is not None:
                    event.wait(stream=stream)

                pinned_input = pinned_input_buffers[chunk % self._stream_count]
                np.copyto(pinned_input, self._traces.samples[:, start:end])

                device_input = cuda.to_device(
                    pinned_input[:, : end - start], stream=stream
                )
                device_outputs = [
                    cuda.device_array(
                        (end - start,), dtype=pinned_input.dtype, stream=stream
                    )
                    for _ in range(output_count)
                ]

                bpg = (end - start + self._tpb - 1) // self._tpb
                func[bpg, self._tpb, stream](
                    device_input, *device_inputs, *device_outputs
                )
                event = cuda.event()
                event.record(stream=stream)
                events[chunk % self._stream_count] = event

                for output_i, device_output in enumerate(device_outputs):
                    # Allocating pinned memory for results
                    host_output = cuda.pinned_array(
                        (end - start,), dtype=pinned_input.dtype
                    )
                    device_output.copy_to_host(host_output, stream=stream)
                    chunk_results[output_i].append(host_output)

            cuda.synchronize()

        return [np.concatenate(chunk_result) for chunk_result in chunk_results]

    def average(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_average))  # type: ignore

    def conditional_average(
        self, cond: Callable[[npt.NDArray[np.number]], bool]
    ) -> CombinedTrace:
        raise NotImplementedError()

    def standard_deviation(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_std_dev))  # type: ignore

    def variance(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_variance))  # type: ignore

    def average_and_variance(self) -> List[CombinedTrace]:
        averages, variances = self._gpu_combine1D(gpu_avg_var, output_count=2)  # type: ignore
        return [averages, variances]

    def add(self) -> CombinedTrace:
        return cast(CombinedTrace, self._gpu_combine1D(gpu_add))  # type: ignore

    def pearson_corr(
        self, intermediate_values: npt.NDArray[np.number]
    ) -> CombinedTrace:
        if len(intermediate_values.shape) != 1 or (
            intermediate_values.shape[0] != self.traces_shape[0]
        ):
            raise ValueError(
                "Intermediate values have to be a vector " "as long as trace_count"
            )
        if np.all(intermediate_values == intermediate_values[0]):
            raise ValueError(
                "Constant intermediate value array, correlation undefined."
            )
        intermed_sum: np.number = np.sum(intermediate_values)
        intermed_sq_sum: np.number = np.sum(np.square(intermediate_values))
        inputs: List[InputType] = [
            intermediate_values,
            np.array([intermed_sum]),
            np.array([intermed_sq_sum]),
        ]

        return cast(CombinedTrace, self._gpu_combine1D(gpu_pearson_corr, inputs))  # type: ignore

    def run(
        self,
        func: Callable,
        inputs: Optional[List[InputType]] = None,
        output_count: int = 1,
    ) -> Union[CombinedTrace, List[CombinedTrace]]:
        return self._gpu_combine1D(func, inputs, output_count)  # type: ignore


@cuda.jit(device=True, cache=True)
def _gpu_average(  # pragma: no cover
    col: int, samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):
    """
    Cuda device thread function computing the average of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    acc = 0.0
    for row in range(samples.shape[0]):
        acc += samples[row, col]
    result[col] = acc / samples.shape[0]


@cuda.jit(cache=True)
def gpu_average(
    samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):  # pragma: no cover
    """
    Sample average of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result)


@cuda.jit(device=True, cache=True)
def _gpu_var_from_avg(  # pragma: no cover
    col: int,
    samples: npt.NDArray[np.number],
    averages: npt.NDArray[np.number],
    result: npt.NDArray[np.number],
):
    """
    Cuda device thread function computing the variance from the average of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param averages: Array of averages of samples.
    :param result: Result output array.
    """
    var = 0.0
    for row in range(samples.shape[0]):
        current = samples[row, col] - averages[col]
        var += current * current
    result[col] = var / samples.shape[0]


@cuda.jit(device=True, cache=True)
def _gpu_variance(  # pragma: no cover
    col: int, samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):
    """
    Cuda device thread function computing the variance of a sample of stacked traces.

    :param col: Index of the sample.
    :param samples: Shared array of the samples of stacked traces.
    :param result: Result output array.
    """
    _gpu_average(col, samples, result)
    _gpu_var_from_avg(col, samples, result, result)


@cuda.jit(cache=True)
def gpu_std_dev(
    samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):  # pragma: no cover
    """
    Sample standard deviation of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)

    result[col] = sqrt(result[col])


@cuda.jit(cache=True)
def gpu_variance(
    samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):  # pragma: no cover
    """
    Sample variance of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:
        return

    _gpu_variance(col, samples, result)


@cuda.jit(cache=True)
def gpu_avg_var(  # pragma: no cover
    samples: npt.NDArray[np.number],
    result_avg: npt.NDArray[np.number],
    result_var: npt.NDArray[np.number],
):
    """
    Sample average and variance of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result_avg: Result average output array.
    :param result_var: Result variance output array.
    """
    col = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:
        return

    _gpu_average(col, samples, result_avg)
    _gpu_var_from_avg(col, samples, result_avg, result_var)


@cuda.jit(cache=True)
def gpu_add(
    samples: npt.NDArray[np.number], result: npt.NDArray[np.number]
):  # pragma: no cover
    """
    Add samples of stacked traces, sample-wise.

    :param samples: Stacked traces' samples.
    :param result: Result output array.
    """
    col = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:
        return

    res = 0.0
    for row in range(samples.shape[0]):
        res += samples[row, col]
    result[col] = res


@cuda.jit(cache=True)
def gpu_pearson_corr(  # pragma: no cover
    samples: DeviceNDArray,
    intermediate_values: DeviceNDArray,
    intermed_sum: DeviceNDArray,
    intermed_sq_sum: DeviceNDArray,
    result: DeviceNDArray,
):
    """
    Calculates the Pearson correlation coefficient between the given samples and intermediate values using GPU acceleration.

    :param samples: A 2D array of shape (n, m) containing the samples.
    :type samples: npt.NDArray[np.number]
    :param intermediate_values: A 1D array of shape (n,) containing the intermediate values.
    :type intermediate_values: npt.NDArray[np.number]
    :param intermed_sum: A 1D array of shape (1,) containing the precomputed sum of the intermediate values.
    :type intermed_sum: npt.NDArray[np.number]
    :param intermed_sq_sum: A 1D array of shape (1,) containing the precomputed sum of the squares of the intermediate values.
    :param result: A 1D array of shape (m,) to store the resulting correlation coefficients.
    :type result: cuda.devicearray.DeviceNDArray
    """
    col: int = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:  # type: ignore
        return

    n = samples.shape[0]
    samples_sum = 0.0
    samples_sq_sum = 0.0
    product_sum = 0.0

    for row in range(n):
        samples_sum += samples[row, col]
        samples_sq_sum += samples[row, col] ** 2
        product_sum += samples[row, col] * intermediate_values[row]

    numerator = float(n) * product_sum - samples_sum * intermed_sum[0]
    denom_samp = sqrt(float(n) * samples_sq_sum - samples_sum**2)
    denom_int = sqrt(float(n) * intermed_sq_sum[0] - intermed_sum[0] ** 2)
    denominator = denom_samp * denom_int

    result[col] = numerator / denominator


@public
class CPUTraceManager(BaseTraceManager):
    """Manager for operations on stacked traces on CPU."""

    def average(self) -> CombinedTrace:
        return CombinedTrace(np.average(self._traces.samples, 0), self._traces.meta)

    def conditional_average(
        self, condition: Callable[[npt.NDArray[np.number]], bool]
    ) -> CombinedTrace:
        # TODO: Consider other ways to implement this
        return CombinedTrace(
            np.average(
                self._traces.samples[
                    np.apply_along_axis(condition, 1, self._traces.samples)
                ],
                1,
            ),
            self._traces.meta,
        )

    def standard_deviation(self) -> CombinedTrace:
        return CombinedTrace(np.std(self._traces.samples, 0), self._traces.meta)

    def variance(self) -> CombinedTrace:
        return CombinedTrace(np.var(self._traces.samples, 0), self._traces.meta)

    def average_and_variance(self) -> List[CombinedTrace]:
        return [self.average(), self.variance()]

    def add(self) -> CombinedTrace:
        return CombinedTrace(np.sum(self._traces.samples, 0), self._traces.meta)

    def pearson_corr(
        self, intermediate_values: npt.NDArray[np.number]
    ) -> CombinedTrace:
        """
        Calculates the Pearson correlation coefficient between the given samples and intermediate values sample-wise.

        The result is equivalent to:

            np.corrcoef(self.traces.samples,
                        intermediate_values,
                        rowvar=False)[-1, :-1]

        but a different implementation is used for better time-efficiency,
        which doesn't compute the whole correlation matrix.

        :param intermediate_values: A 1D array of shape (n,) containing the intermediate values.
        :type intermediate_values: npt.NDArray[np.number]
        """
        samples = self._traces.samples
        n = samples.shape[0]
        if intermediate_values.shape != (n,):
            raise ValueError(
                "Invalid shape of intermediate_values, "
                f"expected ({n},), "
                f"got {intermediate_values.shape}"
            )
        if np.all(intermediate_values == intermediate_values[0]):
            raise ValueError(
                "Constant intermediate value array, correlation undefined."
            )
        new_size = (
            str(samples.dtype.itemsize * 2) if samples.dtype.itemsize != 8 else "8"
        )
        dtype = np.dtype(samples.dtype.kind + new_size)
        sam_sum = np.sum(samples, axis=0)
        sam_sq_sum = np.sum(np.square(samples, dtype=dtype), axis=0)

        iv_sum = np.sum(intermediate_values)
        iv_sq_sum = np.sum(np.square(intermediate_values, dtype=dtype))

        prod_sum = intermediate_values @ samples

        numerator = n * prod_sum - sam_sum * iv_sum
        denom_samp = np.sqrt(n * sam_sq_sum - sam_sum**2)
        denom_int = np.sqrt(n * iv_sq_sum - iv_sum**2)
        denominator = denom_samp * denom_int
        return CombinedTrace(numerator / denominator, self._traces.meta)
