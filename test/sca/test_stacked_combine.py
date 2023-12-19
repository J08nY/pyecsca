import pytest
from numba import cuda

import numpy as np
from pyecsca.sca import (
    StackedTraces,
    GPUTraceManager,
    CombinedTrace
)

TPB = 128
TRACE_COUNT = 2 ** 10
TRACE_LEN = 2 ** 15
RTOL = 1e-5
ATOL = 1e-5
CHUNK_SIZE = 2 ** 5
STREAM_COUNT = 4


@pytest.fixture()
def samples():
    np.random.seed(0x1234)
    return np.random.rand(TRACE_COUNT, TRACE_LEN)


class Base:
    @pytest.fixture()
    def gpu_manager(self):
        raise NotImplementedError("Subclasses should implement this")

    def test_average(self, samples, gpu_manager):
        avg_trace = gpu_manager.average()
        avg_cmp: np.ndarray = np.average(samples, 0)

        assert isinstance(avg_trace, CombinedTrace)
        assert avg_trace.samples.shape == \
            avg_cmp.shape
        assert all(np.isclose(avg_trace.samples, avg_cmp))

    def test_standard_deviation(self, samples, gpu_manager):
        std_trace = gpu_manager.standard_deviation()
        std_cmp: np.ndarray = np.std(samples, 0)

        assert isinstance(std_trace, CombinedTrace)
        assert std_trace.samples.shape == \
            std_cmp.shape
        assert all(np.isclose(std_trace.samples, std_cmp))

    def test_variance(self, samples, gpu_manager):
        var_trace = gpu_manager.variance()
        var_cmp: np.ndarray = np.var(samples, 0)

        assert isinstance(var_trace, CombinedTrace)
        assert var_trace.samples.shape == \
            var_cmp.shape
        assert all(np.isclose(var_trace.samples, var_cmp))

    def test_average_and_variance(self, samples, gpu_manager):
        avg_trace, var_trace = gpu_manager.average_and_variance()
        avg_cmp: np.ndarray = np.average(samples, 0)
        var_cmp: np.ndarray = np.var(samples, 0)

        assert isinstance(avg_trace, CombinedTrace)
        assert isinstance(var_trace, CombinedTrace)
        assert avg_trace.samples.shape == \
            avg_cmp.shape
        assert var_trace.samples.shape == \
            var_cmp.shape
        assert all(np.isclose(avg_trace.samples, avg_cmp))
        assert all(np.isclose(var_trace.samples, var_cmp))

    def test_pearson_coef(self, samples, gpu_manager):
        np.random.seed(0x1234)
        intermediate_values = np.random.rand(TRACE_COUNT)
        corr_gpu = gpu_manager.pearson_corr(intermediate_values)
        corr_cmp = np.corrcoef(
            samples, intermediate_values, rowvar=False)[-1, :-1]

        assert isinstance(corr_gpu, CombinedTrace)
        assert corr_gpu.samples.shape == \
            corr_cmp.shape

        assert all(np.isclose(corr_gpu.samples,
                   corr_cmp, rtol=RTOL, atol=ATOL))


class TestNonChunked(Base):
    @pytest.fixture()
    def gpu_manager(self, samples):
        if not cuda.is_available():
            pytest.skip("CUDA not available")
        return GPUTraceManager(StackedTraces(samples), TPB)


class TestChunked(Base):
    @pytest.fixture()
    def gpu_manager(self, samples):
        if not cuda.is_available():
            pytest.skip("CUDA not available")
        return GPUTraceManager(StackedTraces(samples),
                               TPB,
                               chunk_size=CHUNK_SIZE,
                               stream_count=STREAM_COUNT)
