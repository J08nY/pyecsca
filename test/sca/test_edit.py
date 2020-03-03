from unittest import TestCase

import numpy as np

from pyecsca.sca import Trace, trim, reverse, pad


class EditTests(TestCase):

    def setUp(self):
        self._trace = Trace(np.array([10, 20, 30, 40, 50], dtype=np.dtype("i1")), None, None)

    def test_trim(self):
        result = trim(self._trace, 2)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples, np.array([30, 40, 50], dtype=np.dtype("i1")))

        result = trim(self._trace, end=3)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples, np.array([10, 20, 30], dtype=np.dtype("i1")))

        with self.assertRaises(ValueError):
            trim(self._trace, 5, 1)

    def test_reverse(self):
        result = reverse(self._trace)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples,
                                np.array([50, 40, 30, 20, 10], dtype=np.dtype("i1")))

    def test_pad(self):
        result = pad(self._trace, 2)
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples,
                                np.array([0, 0, 10, 20, 30, 40, 50, 0, 0], dtype=np.dtype("i1")))

        result = pad(self._trace, (1, 3))
        self.assertIsNotNone(result)
        np.testing.assert_equal(result.samples,
                                np.array([0, 10, 20, 30, 40, 50, 0, 0, 0], dtype=np.dtype("i1")))
