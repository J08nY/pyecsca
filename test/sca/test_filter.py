import numpy as np
import pytest

from pyecsca.sca import (
    Trace,
    filter_lowpass,
    filter_highpass,
    filter_bandpass,
    filter_bandstop,
)


@pytest.fixture()
def trace():
    return Trace(
        np.array(
            [5, 12, 15, 13, 15, 11, 7, 2, -4, -8, -10, -8, -13, -9, -11, -8, -5],
            dtype=np.dtype("i1"),
        ),
        None,
    )


def test_lowpass(trace, plot):
    result = filter_lowpass(trace, 100, 20)
    assert result is not None
    assert len(trace.samples) == len(result.samples)
    plot(trace, result)


def test_highpass(trace, plot):
    result = filter_highpass(trace, 128, 20)
    assert result is not None
    assert len(trace.samples) == len(result.samples)
    plot(trace, result)


def test_bandpass(trace, plot):
    result = filter_bandpass(trace, 128, 20, 60)
    assert result is not None
    assert len(trace.samples) == len(result.samples)
    plot(trace, result)


def test_bandstop(trace, plot):
    result = filter_bandstop(trace, 128, 20, 60)
    assert result is not None
    assert len(trace.samples) == len(result.samples)
    plot(trace, result)
