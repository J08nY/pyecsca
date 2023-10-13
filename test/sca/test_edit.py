import numpy as np
import pytest

from pyecsca.sca import Trace, trim, reverse, pad, stretch


@pytest.fixture()
def trace():
    return Trace(np.array([10, 20, 30, 40, 50], dtype=np.dtype("i1")))


def test_trim(trace):
    result = trim(trace, 2)
    assert result is not None
    np.testing.assert_equal(
        result.samples, np.array([30, 40, 50], dtype=np.dtype("i1"))
    )

    result = trim(trace, end=3)
    assert result is not None
    np.testing.assert_equal(
        result.samples, np.array([10, 20, 30], dtype=np.dtype("i1"))
    )

    with pytest.raises(ValueError):
        trim(trace, 5, 1)


def test_reverse(trace):
    result = reverse(trace)
    assert result is not None
    np.testing.assert_equal(
        result.samples, np.array([50, 40, 30, 20, 10], dtype=np.dtype("i1"))
    )


def test_pad(trace):
    result = pad(trace, 2)
    assert result is not None
    np.testing.assert_equal(
        result.samples,
        np.array([0, 0, 10, 20, 30, 40, 50, 0, 0], dtype=np.dtype("i1")),
    )

    result = pad(trace, (1, 3))
    assert result is not None
    np.testing.assert_equal(
        result.samples,
        np.array([0, 10, 20, 30, 40, 50, 0, 0, 0], dtype=np.dtype("i1")),
    )


def test_stretch(trace):
    result = stretch(trace, 10)
    assert result is not None
    assert np.min(result) == min(trace)
    assert np.max(result) == max(trace)
    assert len(result) == 10
