import pytest
from numba import cuda
import numpy as np
from pyecsca.sca import (
    StackedTraces,
    GPUTraceManager,
    CombinedTrace
)
from pyecsca.sca.stacked_traces.correlate import gpu_pearson_corr

TPB = 128
TRACE_COUNT = 2 ** 10
TRACE_LEN = 2 ** 15
RTOL = 1e-5
ATOL = 1e-5


@pytest.fixture()
def samples():
    np.random.seed(0x1234)
    return np.random.rand(TRACE_COUNT, TRACE_LEN).astype(np.float32, order="F")


@pytest.fixture()
def gpu_manager(samples):
    if not cuda.is_available():
        pytest.skip("CUDA not available")
    return GPUTraceManager(StackedTraces(samples), TPB)


@pytest.fixture()
def intermediate_values():
    np.random.seed(0x1234)
    return np.random.rand(TRACE_COUNT)


def pearson_corr(samples, intermediate_values):
    int_sum = np.sum(intermediate_values)
    int_sq_sum = np.sum(np.square(intermediate_values))
    samples_sum = np.sum(samples, axis=0)
    samples_sq_sum = np.sum(np.square(samples), axis=0)
    samples_intermed_sum = np.sum(
        samples * intermediate_values[:, None], axis=0)
    n = samples.shape[0]

    return (n * samples_intermed_sum - int_sum * samples_sum) / \
        (np.sqrt(n * int_sq_sum - int_sum ** 2) *
         np.sqrt(n * samples_sq_sum - np.square(samples_sum)))


def test_pearson_coef_no_chunking(samples, gpu_manager, intermediate_values):
    corr_gpu = gpu_pearson_corr(intermediate_values,
                                trace_manager=gpu_manager)
    corr_cmp = pearson_corr(samples, intermediate_values)

    assert isinstance(corr_gpu, CombinedTrace)
    assert corr_gpu.samples.shape == \
        corr_cmp.shape

    assert all(np.isclose(corr_gpu.samples, corr_cmp, rtol=RTOL, atol=ATOL))


def test_pearson_coef_chunking(samples, gpu_manager, intermediate_values):
    corr_gpu = gpu_pearson_corr(intermediate_values,
                                trace_manager=gpu_manager,
                                chunk_size=2 ** 5,
                                stream_count=4)
    corr_cmp = pearson_corr(samples, intermediate_values)

    assert isinstance(corr_gpu, CombinedTrace)
    assert corr_gpu.samples.shape == \
        corr_cmp.shape

    assert all(np.isclose(corr_gpu.samples, corr_cmp, rtol=RTOL, atol=ATOL))
