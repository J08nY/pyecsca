import pytest
from numba import cuda

import numpy as np
from pyecsca.sca import (
    Trace,
    StackedTraces,
    GPUTraceManager,
    TraceSet,
    CombinedTrace
)

TPB = 128
TRACE_COUNT = 32
TRACE_LEN = 4 * TPB


@pytest.fixture()
def samples():
    np.random.seed(0x1234)
    return np.random.rand(TRACE_COUNT, TRACE_LEN)


@pytest.fixture()
def gpu_manager(samples):
    if not cuda.is_available():
        pytest.skip("CUDA not available")
    return GPUTraceManager(StackedTraces(samples), TPB)


def test_fromarray(samples):
    max_len = samples.shape[1]
    min_len = max_len // 2
    jagged_samples = [
        t[min_len:np.random.randint(max_len)]
        for t
        in samples
    ]
    min_len = min(map(len, jagged_samples))
    stacked = StackedTraces.fromarray(jagged_samples)

    assert isinstance(stacked, StackedTraces)
    assert stacked.samples.shape == \
           (samples.shape[0], min_len)
    assert (stacked.samples == samples[:, :min_len]).all()


def test_fromtraceset(samples):
    max_len = samples.shape[1]
    min_len = max_len // 2
    traces = [
        Trace(t[min_len:np.random.randint(max_len)])
        for t
        in samples
    ]
    tset = TraceSet(*traces)
    min_len = min(map(len, traces))
    stacked = StackedTraces.fromtraceset(tset)

    assert isinstance(stacked, StackedTraces)
    assert stacked.samples.shape == \
           (samples.shape[0], min_len)
    assert (stacked.samples == samples[:, :min_len]).all()


def test_average(samples, gpu_manager):
    avg_trace = gpu_manager.average()
    avg_cmp: np.ndarray = np.average(samples, 0)

    assert isinstance(avg_trace, CombinedTrace)
    assert avg_trace.samples.shape == \
           avg_cmp.shape
    assert all(np.isclose(avg_trace.samples, avg_cmp))


def test_standard_deviation(samples, gpu_manager):
    std_trace = gpu_manager.standard_deviation()
    std_cmp: np.ndarray = np.std(samples, 0)

    assert isinstance(std_trace, CombinedTrace)
    assert std_trace.samples.shape == \
           std_cmp.shape
    assert all(np.isclose(std_trace.samples, std_cmp))


def test_variance(samples, gpu_manager):
    var_trace = gpu_manager.variance()
    var_cmp: np.ndarray = np.var(samples, 0)

    assert isinstance(var_trace, CombinedTrace)
    assert var_trace.samples.shape == \
           var_cmp.shape
    assert all(np.isclose(var_trace.samples, var_cmp))


def test_average_and_variance(samples, gpu_manager):
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
