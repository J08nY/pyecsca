from unittest import TestCase

import numpy as np

from pyecsca.sca import Trace, welch_ttest, student_ttest, ks_test


class TTestTests(TestCase):

    def setUp(self):
        self.a = Trace(np.array([20, 80], dtype=np.dtype("i1")), None, b"\xff", None)
        self.b = Trace(np.array([30, 42], dtype=np.dtype("i1")), None, b"\xff", None)
        self.c = Trace(np.array([78, 56], dtype=np.dtype("i1")), None, b"\x00", None)
        self.d = Trace(np.array([98, 36], dtype=np.dtype("i1")), None, b"\x00", None)

    def test_welch_ttest(self):
        self.assertIsNotNone(welch_ttest([self.a, self.b], [self.c, self.d]))
        a = Trace(np.array([19.8, 20.4, 19.6, 17.8, 18.5, 18.9, 18.3, 18.9, 19.5, 22.0]), None,
                  None, None)
        b = Trace(np.array([28.2, 26.6, 20.1, 23.3, 25.2, 22.1, 17.7, 27.6, 20.6, 13.7]), None,
                  None, None)
        c = Trace(np.array([20.2, 21.6, 27.1, 13.3, 24.2, 20.1, 11.7, 25.6, 26.6, 21.4]), None,
                  None, None)

        result = welch_ttest([a, b], [b, c])
        self.assertIsNotNone(result)

    def test_students_ttest(self):
        self.assertIsNone(student_ttest([], []))
        self.assertIsNotNone(student_ttest([self.a, self.b], [self.c, self.d]))


class KolmogorovSmirnovTests(TestCase):

    def test_ks_test(self):
        self.assertIsNone(ks_test([], []))

        a = Trace(np.array([20, 80], dtype=np.dtype("i1")), None, b"\xff", None)
        b = Trace(np.array([30, 42], dtype=np.dtype("i1")), None, b"\xff", None)
        c = Trace(np.array([78, 56], dtype=np.dtype("i1")), None, b"\x00", None)
        d = Trace(np.array([98, 36], dtype=np.dtype("i1")), None, b"\x00", None)
        self.assertIsNotNone(ks_test([a, b], [c, d]))
