from unittest import TestCase
import numpy as np
from pyecsca.sca import Trace


class TraceTests(TestCase):

    def test_basic(self):
        trace = Trace(np.array([10, 15, 24], dtype=np.dtype("i1")), "Name", b"\xff\xaa")
        self.assertIsNotNone(trace)
        self.assertIn("Trace", str(trace))
        self.assertIsNone(trace.trace_set)
