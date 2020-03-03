from unittest import TestCase

import numpy as np
from pyecsca.sca import Trace, CombinedTrace, average, conditional_average, standard_deviation


class CombineTests(TestCase):

    def setUp(self):
        self.a = Trace(np.array([20, 80], dtype=np.dtype("i1")), None, b"\xff")
        self.b = Trace(np.array([30, 42], dtype=np.dtype("i1")), None, b"\xff")
        self.c = Trace(np.array([78, 56], dtype=np.dtype("i1")), None, b"\x00")

    def test_average(self):
        self.assertIsNone(average())
        result = average(self.a, self.b)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)
        self.assertEqual(result.samples[0], 25)
        self.assertEqual(result.samples[1], 61)

    def test_conditional_average(self):
        result = conditional_average(self.a, self.b, self.c,
                                     condition=lambda trace: trace.data[0] == 0xff)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)
        self.assertEqual(result.samples[0], 25)
        self.assertEqual(result.samples[1], 61)

    def test_standard_deviation(self):
        self.assertIsNone(standard_deviation())
        result = standard_deviation(self.a, self.b)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)
