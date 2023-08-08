import os.path
import shutil
import tempfile
from importlib.resources import files, as_file
from unittest import TestCase

import numpy as np

import test.data.sca
from pyecsca.sca import (
    TraceSet,
    InspectorTraceSet,
    ChipWhispererTraceSet,
    PickleTraceSet,
    HDF5TraceSet,
    Trace,
)

EXAMPLE_TRACES = [
    Trace(np.array([20, 40, 50, 50, 10], dtype=np.dtype("i1")), {"something": 5}),
    Trace(np.array([1, 2, 3, 4, 5], dtype=np.dtype("i1"))),
    Trace(np.array([6, 7, 8, 9, 10], dtype=np.dtype("i1"))),
]
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
        with as_file(files(test.data.sca).joinpath("example.trs")) as path:
            result = InspectorTraceSet.read(path)
            self.assertIsNotNone(result)
            self.assertEqual(result.global_title, "Example trace set")
            self.assertEqual(len(result), 10)
            self.assertEqual(len(list(result)), 10)
            self.assertIn("InspectorTraceSet", str(result))
            self.assertIs(result[0].trace_set, result)
            self.assertEqual(result.sampling_frequency, 12500000)

    def test_load_file(self):
        with files(test.data.sca).joinpath("example.trs").open("rb") as f:
            self.assertIsNotNone(InspectorTraceSet.read(f))

    def test_load_bytes(self):
        with files(test.data.sca).joinpath("example.trs").open("rb") as f:
            self.assertIsNotNone(InspectorTraceSet.read(f.read()))

    def test_save(self):
        with as_file(files(test.data.sca).joinpath("example.trs")) as path:
            trace_set = InspectorTraceSet.read(path)
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.trs")
            trace_set.write(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(InspectorTraceSet.read(path))


class ChipWhispererTraceSetTests(TestCase):
    def test_load_fname(self):
        with as_file(files(test.data.sca).joinpath("config_chipwhisperer_.cfg")) as path:
            # This will not work if the test package is not on the file system directly.
            result = ChipWhispererTraceSet.read(path)
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 2)


class PickleTraceSetTests(TestCase):
    def test_load_fname(self):
        with as_file(files(test.data.sca).joinpath("test.pickle")) as path:
            result = PickleTraceSet.read(path)
            self.assertIsNotNone(result)

    def test_load_file(self):
        with files(test.data.sca).joinpath("test.pickle").open("rb") as f:
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
        with as_file(files(test.data.sca).joinpath("test.h5")) as path:
            result = HDF5TraceSet.read(path)
            self.assertIsNotNone(result)

    def test_load_file(self):
        with files(test.data.sca).joinpath("test.h5").open("rb") as f:
            self.assertIsNotNone(HDF5TraceSet.read(f))

    def test_inplace(self):
        with tempfile.TemporaryDirectory() as dirname, as_file(files(test.data.sca).joinpath("test.h5")) as orig_path:
            path = os.path.join(dirname, "test.h5")
            shutil.copy(orig_path, path)
            trace_set = HDF5TraceSet.inplace(path)
            self.assertIsNotNone(trace_set)
            test_trace = Trace(
                np.array([6, 7], dtype=np.dtype("i1")), meta={"thing": "ring"}
            )
            other_trace = Trace(
                np.array([15, 7], dtype=np.dtype("i1")), meta={"a": "b"}
            )
            trace_set.append(test_trace)
            self.assertEqual(len(trace_set), 4)
            trace_set.append(other_trace)
            trace_set.remove(other_trace)
            self.assertEqual(len(trace_set), 4)
            trace_set.save()
            trace_set.close()

            test_set = HDF5TraceSet.read(path)
            self.assertEqual(test_set.get(3), test_set[3])
            self.assertTrue(np.array_equal(test_set[3].samples, test_trace.samples))
            self.assertEqual(test_set[3].meta["thing"], test_trace.meta["thing"])
            self.assertEqual(test_set[3], test_trace)

    def test_save(self):
        trace_set = HDF5TraceSet(*EXAMPLE_TRACES, **EXAMPLE_KWARGS)
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.h5")
            trace_set.write(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(HDF5TraceSet.read(path))
