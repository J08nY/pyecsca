from unittest import TestCase

import numpy as np

from pyecsca.sca import Trace, welch_ttest, student_ttest, ks_test


class TTestTests(TestCase):

    def setUp(self):
        self.a = Trace(None, b"\xff", np.array([20, 80], dtype=np.dtype("i1")))
        self.b = Trace(None, b"\xff", np.array([30, 42], dtype=np.dtype("i1")))
        self.c = Trace(None, b"\x00", np.array([78, 56], dtype=np.dtype("i1")))
        self.d = Trace(None, b"\x00", np.array([98, 36], dtype=np.dtype("i1")))

    def test_welch_ttest(self):
        self.assertIsNotNone(welch_ttest([self.a, self.b], [self.c, self.d]))
        a = Trace(None, None, np.array([19.8, 20.4, 19.6, 17.8, 18.5, 18.9, 18.3, 18.9, 19.5, 22.0]))
        b = Trace(None, None, np.array([28.2, 26.6, 20.1, 23.3, 25.2, 22.1, 17.7, 27.6, 20.6, 13.7]))
        c = Trace(None, None, np.array([20.2, 21.6, 27.1, 13.3, 24.2, 20.1, 11.7, 25.6, 26.6, 21.4]))

        result = welch_ttest([a, b], [b, c])
        self.assertIsNotNone(result)

    def test_students_ttest(self):
        self.assertIsNone(student_ttest([], []))
        self.assertIsNotNone(student_ttest([self.a, self.b], [self.c, self.d]))


class KolmogorovSmirnovTests(TestCase):

    def test_ks_test(self):
        self.assertIsNone(ks_test([], []))

        a = Trace(None, b"\xff", np.array([20, 80], dtype=np.dtype("i1")))
        b = Trace(None, b"\xff", np.array([30, 42], dtype=np.dtype("i1")))
        c = Trace(None, b"\x00", np.array([78, 56], dtype=np.dtype("i1")))
        d = Trace(None, b"\x00", np.array([98, 36], dtype=np.dtype("i1")))
        self.assertIsNotNone(ks_test([a, b], [c, d]))
