from unittest import TestCase

import numpy as np
from pyecsca.sca import Trace, filter_lowpass, filter_highpass, filter_bandpass, filter_bandstop
from .utils import plot


class FilterTests(TestCase):

    def setUp(self):
        self._trace = Trace(
            np.array([5, 12, 15, 13, 15, 11, 7, 2, -4, -8, -10, -8, -13, -9, -11, -8, -5],
                     dtype=np.dtype("i1")), None, None)

    def test_lowpass(self):
        result = filter_lowpass(self._trace, 100, 20)
        self.assertIsNotNone(result)
        self.assertEqual(len(self._trace.samples), len(result.samples))
        plot(self, self._trace, result)

    def test_highpass(self):
        result = filter_highpass(self._trace, 128, 20)
        self.assertIsNotNone(result)
        self.assertEqual(len(self._trace.samples), len(result.samples))
        plot(self, self._trace, result)

    def test_bandpass(self):
        result = filter_bandpass(self._trace, 128, 20, 60)
        self.assertIsNotNone(result)
        self.assertEqual(len(self._trace.samples), len(result.samples))
        plot(self, self._trace, result)

    def test_bandstop(self):
        result = filter_bandstop(self._trace, 128, 20, 60)
        self.assertIsNotNone(result)
        self.assertEqual(len(self._trace.samples), len(result.samples))
        plot(self, self._trace, result)
