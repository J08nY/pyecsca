import numpy as np
from pyecsca.sca import align_correlation, align_peaks, align_sad, align_dtw_scale,\
    align_dtw, Trace, InspectorTraceSet
from .utils import Plottable, slow


class AlignTests(Plottable):

    def test_align(self):
        first_arr = np.array([10, 64, 120, 64, 10, 10, 10, 10, 10], dtype=np.dtype("i1"))
        second_arr = np.array([10, 10, 10, 10, 50, 80, 50, 20], dtype=np.dtype("i1"))
        third_arr = np.array([70, 30, 42, 35, 28, 21, 15, 10, 5], dtype=np.dtype("i1"))
        a = Trace(first_arr)
        b = Trace(second_arr)
        c = Trace(third_arr)
        result, offsets = align_correlation(a, b, c, reference_offset=1, reference_length=3, max_offset=4, min_correlation=0.65)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        np.testing.assert_equal(result[0].samples, first_arr)
        np.testing.assert_equal(result[1].samples, np.array([10, 50, 80, 50, 20, 0, 0, 0], dtype=np.dtype("i1")))

    @slow
    def test_large_align(self):
        example = InspectorTraceSet.read("test/data/example.trs")
        result, offsets = align_correlation(*example, reference_offset=100000, reference_length=20000, max_offset=15000)
        self.assertIsNotNone(result)

    @slow
    def test_large_dtw_align(self):
        example = InspectorTraceSet.read("test/data/example.trs")
        result = align_dtw(*example[:5])
        self.assertIsNotNone(result)

    def test_peak_align(self):
        first_arr = np.array([10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10], dtype=np.dtype("i1"))
        second_arr = np.array([10, 10, 10, 10, 90, 40, 50, 20, 10, 17, 16, 10], dtype=np.dtype("i1"))
        a = Trace(first_arr)
        b = Trace(second_arr)
        result, offsets = align_peaks(a, b, reference_offset=2, reference_length=5, max_offset=3)
        self.assertEqual(np.argmax(result[0].samples), np.argmax(result[1].samples))

    def test_sad_align(self):
        first_arr = np.array([10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10], dtype=np.dtype("i1"))
        second_arr = np.array([10, 10, 90, 40, 50, 20, 10, 17, 16, 10, 10], dtype=np.dtype("i1"))
        a = Trace(first_arr)
        b = Trace(second_arr)
        result, offsets = align_sad(a, b, reference_offset=2, reference_length=5, max_offset=3)
        self.assertEqual(len(result), 2)

    def test_dtw_align_scale(self):
        first_arr = np.array([10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10, 8, 10, 12, 10, 13, 9], dtype=np.dtype("f2"))
        second_arr = np.array([10, 10, 60, 40, 90, 20, 10, 17, 16, 10, 10, 10, 10, 10, 17, 12, 10], dtype=np.dtype("f2"))
        third_arr = np.array([10, 30, 20, 21, 15, 8, 10, 37, 21, 77, 20, 28, 25, 10, 9, 10, 15, 9, 10], dtype=np.dtype("f2"))
        a = Trace(first_arr)
        b = Trace(second_arr)
        c = Trace(third_arr)
        result = align_dtw_scale(a, b, c)

        self.assertEqual(np.argmax(result[0].samples), np.argmax(result[1].samples))
        self.assertEqual(np.argmax(result[1].samples), np.argmax(result[2].samples))
        self.plot(*result)

        result_other = align_dtw_scale(a, b, c, fast=False)

        self.assertEqual(np.argmax(result_other[0].samples), np.argmax(result_other[1].samples))
        self.assertEqual(np.argmax(result_other[1].samples), np.argmax(result_other[2].samples))
        self.plot(*result_other)

    def test_dtw_align(self):
        first_arr = np.array([10, 64, 14, 120, 15, 30, 10, 15, 20, 15, 15, 10, 10, 8, 10, 12, 10, 13, 9], dtype=np.dtype("i1"))
        second_arr = np.array([10, 10, 60, 40, 90, 20, 10, 17, 16, 10, 10, 10, 10, 10, 17, 12, 10], dtype=np.dtype("i1"))
        third_arr = np.array([10, 30, 20, 21, 15, 8, 10, 47, 21, 77, 20, 28, 25, 10, 9, 10, 15, 9, 10], dtype=np.dtype("i1"))
        a = Trace(first_arr)
        b = Trace(second_arr)
        c = Trace(third_arr)
        result = align_dtw(a, b, c)

        self.assertEqual(np.argmax(result[0].samples), np.argmax(result[1].samples))
        self.assertEqual(np.argmax(result[1].samples), np.argmax(result[2].samples))
        self.plot(*result)

        result_other = align_dtw(a, b, c, fast=False)

        self.assertEqual(np.argmax(result_other[0].samples), np.argmax(result_other[1].samples))
        self.assertEqual(np.argmax(result_other[1].samples), np.argmax(result_other[2].samples))
        self.plot(*result_other)
