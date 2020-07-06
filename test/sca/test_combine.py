from unittest import TestCase

import numpy as np
from pyecsca.sca import Trace, CombinedTrace, average, conditional_average, standard_deviation, variance, average_and_variance, add, subtract


class CombineTests(TestCase):

    def setUp(self):
        self.a = Trace(np.array([20, 80], dtype=np.dtype("i1")), {"data": b"\xff"})
        self.b = Trace(np.array([30, 42], dtype=np.dtype("i1")), {"data": b"\xff"})
        self.c = Trace(np.array([78, 56], dtype=np.dtype("i1")), {"data": b"\x00"})

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
                                     condition=lambda trace: trace.meta["data"] == b"\xff")
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)
        self.assertEqual(result.samples[0], 25)
        self.assertEqual(result.samples[1], 61)

    def test_standard_deviation(self):
        self.assertIsNone(standard_deviation())
        result = standard_deviation(self.a, self.b)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)

    def test_variance(self):
        self.assertIsNone(variance())
        result = variance(self.a, self.b)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(len(result.samples), 2)

    def test_average_and_variance(self):
        self.assertIsNone(average_and_variance())
        mean, var = average_and_variance(self.a, self.b)
        self.assertIsInstance(mean, CombinedTrace)
        self.assertIsInstance(var, CombinedTrace)
        self.assertEqual(len(mean.samples), 2)
        self.assertEqual(len(var.samples), 2)
        self.assertEqual(mean, average(self.a, self.b))
        self.assertEqual(var, variance(self.a, self.b))

    def test_add(self):
        self.assertIsNone(add())
        result = add(self.a, self.b)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(result.samples[0], 50)
        self.assertEqual(result.samples[1], 122)
        np.testing.assert_equal(self.a.samples, add(self.a).samples)

    def test_subtract(self):
        result = subtract(self.a, self.b)
        self.assertIsInstance(result, CombinedTrace)
        self.assertEqual(result.samples[0], -10)
        self.assertEqual(result.samples[1], 38)

