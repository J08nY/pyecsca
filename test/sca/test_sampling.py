from unittest import TestCase

import numpy as np
from pyecsca.sca import Trace, downsample_average, downsample_pick, downsample_decimate
from .utils import plot


class SamplingTests(TestCase):

    def setUp(self):
        self._trace = Trace(None, None, np.array([20, 40, 50, 50, 10], dtype=np.dtype("i1")))

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

    def test_downsample_decimate(self):
        trace = Trace(None, None, np.array([20, 30, 55, 18, 15, 10, 35, 24, 21, 15, 10, 8, -10, -5,
                                            -8, -12, -15, -18, -34, -21, -17, -10, -5, -12, -6, -2,
                                            4, 8, 21, 28], dtype=np.dtype("i1")))
        result = downsample_decimate(trace, 2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Trace)
        self.assertEqual(len(result.samples), 15)
        plot(self, trace, result)
