import numpy as np
import pytest
from importlib_resources import files, as_file
from pyecsca.sca import (
    align_correlation,
    align_peaks,
    align_sad,
    align_dtw_scale,
    align_dtw,
    Trace,
    InspectorTraceSet,
)
import test.data.sca


def test_align():
    first_arr = np.array(
        [10, 64, 120, 64, 10, 10, 10, 10, 10], dtype=np.dtype("i1")
    )
    second_arr = np.array([10, 10, 10, 10, 50, 80, 50, 20], dtype=np.dtype("i1"))
    third_arr = np.array([70, 30, 42, 35, 28, 21, 15, 10, 5], dtype=np.dtype("i1"))
    a = Trace(first_arr)
    b = Trace(second_arr)
    c = Trace(third_arr)
    result, offsets = align_correlation(
        a,
        b,
        c,
        reference_offset=1,
        reference_length=3,
        max_offset=4,
        min_correlation=0.65,
    )
    assert result is not None
    assert len(result) == 2
    np.testing.assert_equal(result[0].samples, first_arr)
    np.testing.assert_equal(
        result[1].samples,
        np.array([10, 50, 80, 50, 20, 0, 0, 0], dtype=np.dtype("i1")),
    )
    assert len(offsets) == 2
    assert offsets[0] == 0
    assert offsets[1] == 3


@pytest.mark.slow
def test_large_align():
    with as_file(files(test.data.sca).joinpath("example.trs")) as path:
        example = InspectorTraceSet.read(path)
        result, _ = align_correlation(
            *example, reference_offset=100000, reference_length=20000, max_offset=15000
        )
        assert result is not None


@pytest.mark.slow
def test_large_dtw_align():
    with as_file(files(test.data.sca).joinpath("example.trs")) as path:
        example = InspectorTraceSet.read(path)
        result = align_dtw(*example[:5])
        assert result is not None


def test_peak_align():
    first_arr = np.array(
        [10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10], dtype=np.dtype("i1")
    )
    second_arr = np.array(
        [10, 10, 10, 10, 90, 40, 50, 20, 10, 17, 16, 10], dtype=np.dtype("i1")
    )
    a = Trace(first_arr)
    b = Trace(second_arr)
    result, _ = align_peaks(
        a, b, reference_offset=2, reference_length=5, max_offset=3
    )
    assert np.argmax(result[0].samples) == np.argmax(result[1].samples)


def test_sad_align():
    first_arr = np.array(
        [10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10], dtype=np.dtype("i1")
    )
    second_arr = np.array(
        [10, 10, 90, 40, 50, 20, 10, 17, 16, 10, 10], dtype=np.dtype("i1")
    )
    a = Trace(first_arr)
    b = Trace(second_arr)
    result, _ = align_sad(
        a, b, reference_offset=2, reference_length=5, max_offset=3
    )
    assert len(result) == 2


def test_dtw_align(plot):
    first_arr = np.array(
        [10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10, 8, 10, 12, 10, 13, 9],
        dtype=np.dtype("i1"),
    )
    second_arr = np.array(
        [10, 10, 60, 40, 90, 20, 10, 17, 16, 10, 10, 10, 10, 10, 17, 12, 10],
        dtype=np.dtype("i1"),
    )
    third_arr = np.array(
        [10, 30, 20, 21, 15, 8, 10, 47, 21, 77, 20, 28, 25, 10, 9, 10, 15, 9, 10],
        dtype=np.dtype("i1"),
    )
    a = Trace(first_arr)
    b = Trace(second_arr)
    c = Trace(third_arr)
    result = align_dtw(a, b, c)

    assert np.argmax(result[0].samples) == np.argmax(result[1].samples)
    assert np.argmax(result[1].samples) == np.argmax(result[2].samples)
    plot(*result)

    result_other = align_dtw(a, b, c, fast=False)

    assert np.argmax(result_other[0].samples) == np.argmax(result_other[1].samples)
    assert np.argmax(result_other[1].samples) == np.argmax(result_other[2].samples)
    plot(*result_other)


def test_dtw_align_scale(plot):
    first_arr = np.array(
        [10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10, 8, 10, 12, 10, 13, 9],
        dtype=np.dtype("f2"),
    )
    second_arr = np.array(
        [10, 10, 60, 40, 90, 20, 10, 17, 16, 10, 10, 10, 10, 10, 17, 12, 10],
        dtype=np.dtype("f2"),
    )
    third_arr = np.array(
        [10, 30, 20, 21, 15, 8, 10, 37, 21, 77, 20, 28, 25, 10, 9, 10, 15, 9, 10],
        dtype=np.dtype("f2"),
    )
    a = Trace(first_arr)
    b = Trace(second_arr)
    c = Trace(third_arr)
    result = align_dtw_scale(a, b, c)

    assert np.argmax(result[0].samples) == np.argmax(result[1].samples)
    assert np.argmax(result[1].samples) == np.argmax(result[2].samples)
    plot(*result)

    result_other = align_dtw_scale(a, b, c, fast=False)

    assert np.argmax(result_other[0].samples) == np.argmax(result_other[1].samples)
    assert np.argmax(result_other[1].samples) == np.argmax(result_other[2].samples)
    plot(*result_other)
