from collections import namedtuple
import numpy as np
import pytest

from pyecsca.sca import (
    Trace,
    CombinedTrace,
    average,
    conditional_average,
    standard_deviation,
    variance,
    average_and_variance,
    add,
    subtract,
)


@pytest.fixture()
def data():
    Data = namedtuple("Data", ["a", "b", "c"])
    return Data(a=Trace(np.array([20, 80], dtype=np.dtype("i1")), {"data": b"\xff"}),
                b=Trace(np.array([30, 42], dtype=np.dtype("i1")), {"data": b"\xff"}),
                c=Trace(np.array([78, 56], dtype=np.dtype("i1")), {"data": b"\x00"}))


def test_average(data):
    with pytest.raises(ValueError):
        average()
    result = average(data.a, data.b)
    assert result is not None
    assert isinstance(result, CombinedTrace)
    assert len(result.samples) == 2
    assert result.samples[0] == 25
    assert result.samples[1] == 61


def test_conditional_average(data):
    result = conditional_average(data.a, data.b, data.c, condition=lambda trace: trace.meta["data"] == b"\xff", )
    assert isinstance(result, CombinedTrace)
    assert len(result.samples) == 2
    assert result.samples[0] == 25
    assert result.samples[1] == 61


def test_standard_deviation(data):
    with pytest.raises(ValueError):
        standard_deviation()
    result = standard_deviation(data.a, data.b)
    assert isinstance(result, CombinedTrace)
    assert len(result.samples) == 2


def test_variance(data):
    with pytest.raises(ValueError):
        variance()
    result = variance(data.a, data.b)
    assert isinstance(result, CombinedTrace)
    assert len(result.samples) == 2


def test_average_and_variance(data):
    with pytest.raises(ValueError):
        average_and_variance()
    mean, var = average_and_variance(data.a, data.b)
    assert isinstance(mean, CombinedTrace)
    assert isinstance(var, CombinedTrace)
    assert len(mean.samples) == 2
    assert len(var.samples) == 2
    assert mean == average(data.a, data.b)
    assert var == variance(data.a, data.b)


def test_add(data):
    with pytest.raises(ValueError):
        add()
    result = add(data.a, data.b)
    assert isinstance(result, CombinedTrace)
    assert result.samples[0] == 50
    assert result.samples[1] == 122
    np.testing.assert_equal(data.a.samples, add(data.a).samples)


def test_subtract(data):
    result = subtract(data.a, data.b)
    assert isinstance(result, CombinedTrace)
    assert result.samples[0] == -10
    assert result.samples[1] == 38
