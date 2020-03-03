from unittest import TestCase
from os.path import realpath, dirname, join


from pyecsca.sca.target import BinaryTarget, SimpleSerialTarget, SimpleSerialMessage

class TestTarget(SimpleSerialTarget, BinaryTarget):
    pass

class BinaryTargetTests(TestCase):

    def test_basic_target(self):
        target_path = join(dirname(realpath(__file__)), "..", "data", "target.py")
        target = TestTarget(["python", target_path])
        target.connect()
        resp = target.send_cmd(SimpleSerialMessage("d", ""), 500)
        self.assertIn("r", resp)
        self.assertIn("z", resp)
        self.assertEqual(resp["r"].data, "01020304")
        target.disconnect()