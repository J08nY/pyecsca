from unittest import TestCase
import os.path
import tempfile

from pyecsca.sca import TraceSet, InspectorTraceSet, ChipWhispererTraceSet


class TraceSetTests(TestCase):

    def test_create(self):
        self.assertIsNotNone(TraceSet())
        self.assertIsNotNone(InspectorTraceSet())
        self.assertIsNotNone(ChipWhispererTraceSet())


class InspectorTraceSetTests(TestCase):

    def test_load_fname(self):
        result = InspectorTraceSet("test/data/example.trs")
        self.assertIsNotNone(result)
        self.assertEqual(result.global_title, "Example trace set")
        self.assertEqual(len(result), 10)
        self.assertIn("InspectorTraceSet", str(result))
        self.assertIs(result[0].trace_set, result)
        self.assertEqual(result.sampling_frequency, 12500000)

    def test_load_file(self):
        with open("test/data/example.trs", "rb") as f:
            self.assertIsNotNone(InspectorTraceSet(f))

    def test_load_bytes(self):
        with open("test/data/example.trs", "rb") as f:
            self.assertIsNotNone(InspectorTraceSet(f.read()))

    def test_get_bytes(self):
        self.assertIsNotNone(bytes(InspectorTraceSet("test/data/example.trs")))

    def test_keep_traces(self):
        trace_set = InspectorTraceSet("test/data/example.trs")
        self.assertIsNotNone(trace_set.raw)
        trace_set = InspectorTraceSet("test/data/example.trs", keep_raw_traces=False)
        self.assertIsNone(trace_set.raw)

    def test_save(self):
        trace_set = InspectorTraceSet("test/data/example.trs")
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.trs")
            trace_set.save(path)
            self.assertTrue(os.path.exists(path))
            self.assertIsNotNone(InspectorTraceSet(path))


class ChipWhispererTraceSetTest(TestCase):

    def test_load_fname(self):
        result = ChipWhispererTraceSet("test/data/", "chipwhisperer")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
