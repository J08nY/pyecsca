from unittest import TestCase

import numpy as np
from pyecsca.sca import Trace, absolute, invert, threshold, rolling_mean, offset, recenter, normalize, normalize_wl


class ProcessTests(TestCase):

    def setUp(self):
        self._trace = Trace(np.array([30, -60, 145, 247], dtype=np.dtype("i2")), None)

    def test_absolute(self):
        result = absolute(self._trace)
        self.assertIsNotNone(result)
        self.assertEqual(result.samples[1], 60)

    def test_invert(self):
        result = invert(self._trace)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples, [-30, 60, -145, -247])

    def test_threshold(self):
        result = threshold(self._trace, 128)
        self.assertIsNotNone(result)
        self.assertEqual(result.samples[0], 0)
        self.assertEqual(result.samples[2], 1)

    def test_rolling_mean(self):
        result = rolling_mean(self._trace, 2)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.samples), 3)
        self.assertEqual(result.samples[0], -15)
        self.assertEqual(result.samples[1], 42)
        self.assertEqual(result.samples[2], 196)

    def test_offset(self):
        result = offset(self._trace, 5)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples, np.array([35, -55, 150, 252], dtype=np.dtype("i2")))

    def test_recenter(self):
        self.assertIsNotNone(recenter(self._trace))

    def test_normalize(self):
        result = normalize(self._trace)
        self.assertIsNotNone(result)

    def test_normalize_wl(self):
        result = normalize_wl(self._trace)
        self.assertIsNotNone(result)
