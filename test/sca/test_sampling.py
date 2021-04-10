import numpy as np
from pyecsca.sca import (
    Trace,
    downsample_average,
    downsample_pick,
    downsample_decimate,
    downsample_max,
    downsample_min,
)
from .utils import Plottable


class SamplingTests(Plottable):
    def setUp(self):
        self._trace = Trace(np.array([20, 40, 50, 50, 10], dtype=np.dtype("i1")))

    def test_downsample_average(self):
        result = downsample_average(self._trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 2)
        self.assertEqual(result.samples[0], 30)
        self.assertEqual(result.samples[1], 50)

    def test_downsample_pick(self):
        result = downsample_pick(self._trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 3)
        self.assertEqual(result.samples[0], 20)
        self.assertEqual(result.samples[1], 50)

    def test_downsample_max(self):
        trace = Trace(
            np.array(
                [
                    20,
                    30,
                    55,
                    18,
                    15,
                    10,
                    35,
                    24,
                    21,
                    15,
                    10,
                    8,
                    -10,
                    -5,
                    -8,
                    -12,
                    -15,
                    -18,
                    -34,
                    -21,
                    -17,
                    -10,
                    -5,
                    -12,
                    -6,
                    -2,
                    4,
                    8,
                    21,
                    28,
                ],
                dtype=np.dtype("i1"),
            )
        )
        result = downsample_max(trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 15)
        self.assertEqual(
            list(result), [30, 55, 15, 35, 21, 10, -5, -8, -15, -21, -10, -5, -2, 8, 28]
        )

    def test_downsample_min(self):
        trace = Trace(
            np.array(
                [
                    20,
                    30,
                    55,
                    18,
                    15,
                    10,
                    35,
                    24,
                    21,
                    15,
                    10,
                    8,
                    -10,
                    -5,
                    -8,
                    -12,
                    -15,
                    -18,
                    -34,
                    -21,
                    -17,
                    -10,
                    -5,
                    -12,
                    -6,
                    -2,
                    4,
                    8,
                    21,
                    28,
                ],
                dtype=np.dtype("i1"),
            )
        )
        result = downsample_min(trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 15)
        self.assertEqual(
            list(result),
            [20, 18, 10, 24, 15, 8, -10, -12, -18, -34, -17, -12, -6, 4, 21],
        )

    def test_downsample_decimate(self):
        trace = Trace(
            np.array(
                [
                    20,
                    30,
                    55,
                    18,
                    15,
                    10,
                    35,
                    24,
                    21,
                    15,
                    10,
                    8,
                    -10,
                    -5,
                    -8,
                    -12,
                    -15,
                    -18,
                    -34,
                    -21,
                    -17,
                    -10,
                    -5,
                    -12,
                    -6,
                    -2,
                    4,
                    8,
                    21,
                    28,
                ],
                dtype=np.dtype("i1"),
            )
        )
        result = downsample_decimate(trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 15)
        self.plot(trace, result)
