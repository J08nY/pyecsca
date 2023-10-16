import numpy as np
import pytest

from pyecsca.sca import (
    Trace,
    absolute,
    invert,
    threshold,
    rolling_mean,
    offset,
    recenter,
    normalize,
    normalize_wl,
    transform
)


@pytest.fixture()
def trace():
    return Trace(np.array([30, -60, 145, 247], dtype=np.dtype("i2")), None)


def test_absolute(trace):
    result = absolute(trace)
    assert result is not None
    assert result.samples[1] == 60


def test_invert(trace):
    result = invert(trace)
    assert result is not None
    np.testing.assert_equal(result.samples, [-30, 60, -145, -247])


def test_threshold(trace):
    result = threshold(trace, 128)
    assert result is not None
    assert result.samples[0] == 0
    assert result.samples[2] == 1


def test_rolling_mean(trace):
    result = rolling_mean(trace, 2)
    assert result is not None
    assert len(result.samples) == 3
    assert result.samples[0] == -15
    assert result.samples[1] == 42.5
    assert result.samples[2] == 196


def test_offset(trace):
    result = offset(trace, 5)
    assert result is not None
    np.testing.assert_equal(
        result.samples, np.array([35, -55, 150, 252], dtype=np.dtype("i2"))
    )


def test_recenter(trace):
    assert recenter(trace) is not None


def test_normalize(trace):
    result = normalize(trace)
    assert result is not None
    assert np.isclose(0, np.mean(result.samples))
    assert np.isclose(1, np.var(result.samples))


def test_normalize_wl(trace):
    result = normalize_wl(trace)
    assert result is not None
    assert np.isclose(0, np.mean(result.samples))
    assert np.isclose(1/len(result), np.std(result.samples))


def test_transform(trace):
    result = transform(trace, 5, 10)
    assert result is not None
    assert min(result) == 5
    assert max(result) == 10
