import os.path
import shutil
import tempfile
from unittest import TestCase

import numpy as np

from pyecsca.sca import (TraceSet, InspectorTraceSet, ChipWhispererTraceSet, PickleTraceSet,
                         HDF5TraceSet, Trace)

EXAMPLE_TRACES = [Trace(np.array([20, 40, 50, 50, 10], dtype=np.dtype("i1")), None, None),
                  Trace(np.array([1, 2, 3, 4, 5], dtype=np.dtype("i1")), None, None),
                  Trace(np.array([6, 7, 8, 9, 10], dtype=np.dtype("i1")), None, None)]
EXAMPLE_KWARGS = {"num_traces": 3, "thingy": "abc"}


class TraceSetTests(TestCase):

    def test_create(self):
        self.assertIsNotNone(TraceSet())
        self.assertIsNotNone(InspectorTraceSet())
        self.assertIsNotNone(ChipWhispererTraceSet())
        self.assertIsNotNone(PickleTraceSet())
        self.assertIsNotNone(HDF5TraceSet())


class InspectorTraceSetTests(TestCase):

    def test_load_fname(self):
        result = InspectorTraceSet.read("test/data/example.trs")
        self.assertIsNotNone(result)
        self.assertEqual(result.global_title, "Example trace set")
        self.assertEqual(len(result), 10)
        self.assertEqual(len(list(result)), 10)
        self.assertIn("InspectorTraceSet", str(result))
        self.assertIs(result[0].trace_set, result)
        self.assertEqual(result.sampling_frequency, 12500000)

    def test_load_file(self):
        with open("test/data/example.trs", "rb") as f:
            self.assertIsNotNone(InspectorTraceSet.read(f))

    def test_load_bytes(self):
        with open("test/data/example.trs", "rb") as f:
            self.assertIsNotNone(InspectorTraceSet.read(f.read()))

    def test_save(self):
        trace_set = InspectorTraceSet.read("test/data/example.trs")
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.trs")
            trace_set.write(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(InspectorTraceSet.read(path))


class ChipWhispererTraceSetTests(TestCase):

    def test_load_fname(self):
        result = ChipWhispererTraceSet.read("test/data/config_chipwhisperer_.cfg")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)


class PickleTraceSetTests(TestCase):

    def test_load_fname(self):
        result = PickleTraceSet.read("test/data/test.pickle")
        self.assertIsNotNone(result)

    def test_load_file(self):
        with open("test/data/test.pickle", "rb") as f:
            self.assertIsNotNone(PickleTraceSet.read(f))

    def test_save(self):
        trace_set = PickleTraceSet(*EXAMPLE_TRACES, **EXAMPLE_KWARGS)
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.pickle")
            trace_set.write(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(PickleTraceSet.read(path))


class HDF5TraceSetTests(TestCase):

    def test_load_fname(self):
        result = HDF5TraceSet.read("test/data/test.h5")
        self.assertIsNotNone(result)

    def test_load_file(self):
        with open("test/data/test.h5", "rb") as f:
            self.assertIsNotNone(HDF5TraceSet.read(f))

    def test_inplace(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "test.h5")
            shutil.copy("test/data/test.h5", path)
            trace_set = HDF5TraceSet.inplace(path)
            self.assertIsNotNone(trace_set)
            test_trace = Trace(np.array([6, 7], dtype=np.dtype("i1")), None, None, meta={"thing": "ring"})
            trace_set[0] = test_trace
            trace_set.save()
            trace_set.close()

            test_set = HDF5TraceSet.read(path)
            self.assertEquals(test_set[0], test_trace)

    def test_save(self):
        trace_set = HDF5TraceSet(*EXAMPLE_TRACES, **EXAMPLE_KWARGS)
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.h5")
            trace_set.write(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(HDF5TraceSet.read(path))
