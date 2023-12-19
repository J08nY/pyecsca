import pytest
import numpy as np
from pyecsca.sca import (
    Trace,
    StackedTraces,
    TraceSet,
)


TRACE_COUNT = 2 ** 10
TRACE_LEN = 2 ** 15


@pytest.fixture()
def samples():
    np.random.seed(0x1234)
    return np.random.rand(TRACE_COUNT, TRACE_LEN)


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
