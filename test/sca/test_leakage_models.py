from unittest import TestCase

from pyecsca.ec.context import local, DefaultContext
from pyecsca.ec.formula import FormulaAction, OpResult
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.op import OpType
from pyecsca.ec.params import get_params
from pyecsca.sca.attack.leakage_model import Identity, Bit, Slice, HammingWeight, HammingDistance, BitLength


class LeakageModelTests(TestCase):

    def test_identity(self):
        val = Mod(3, 7)
        lm = Identity()
        self.assertEqual(lm(val), 3)

    def test_bit(self):
        val = Mod(3, 7)
        lm = Bit(0)
        self.assertEqual(lm(val), 1)
        lm = Bit(4)
        self.assertEqual(lm(val), 0)
        with self.assertRaises(ValueError):
            Bit(-3)

    def test_slice(self):
        val = Mod(0b11110000, 0xf00)
        lm = Slice(0, 4)
        self.assertEqual(lm(val), 0)
        lm = Slice(1, 5)
        self.assertEqual(lm(val), 0b1000)
        lm = Slice(4, 8)
        self.assertEqual(lm(val), 0b1111)
        with self.assertRaises(ValueError):
            Slice(7, 1)

    def test_hamming_weight(self):
        val = Mod(0b11110000, 0xf00)
        lm = HammingWeight()
        self.assertEqual(lm(val), 4)

    def test_hamming_distance(self):
        a = Mod(0b11110000, 0xf00)
        b = Mod(0b00010000, 0xf00)
        lm = HammingDistance()
        self.assertEqual(lm(a, b), 3)

    def test_bit_length(self):
        a = Mod(0b11110000, 0xf00)
        lm = BitLength()
        self.assertEqual(lm(a), 8)


class ModelTraceTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.add = self.coords.formulas["add-1998-cmo"]
        self.dbl = self.coords.formulas["dbl-1998-cmo"]
        self.neg = self.coords.formulas["neg"]
        self.scale = self.coords.formulas["z"]

    def test_mult_hw(self):
        scalar = 0x123456789
        mult = LTRMultiplier(
            self.add,
            self.dbl,
            self.scale,
            always=True,
            complete=False,
            short_circuit=True,
        )
        with local(DefaultContext()) as ctx:
            mult.init(self.secp128r1, self.base)
            mult.multiply(scalar)

        lm = HammingWeight()
        trace = []

        def callback(action):
            if isinstance(action, FormulaAction):
                for intermediate in action.op_results:
                    leak = lm(intermediate.value)
                    trace.append(leak)

        ctx.actions.walk(callback)
        self.assertGreater(len(trace), 0)

    def test_mult_hd(self):
        scalar = 0x123456789
        mult = LTRMultiplier(
            self.add,
            self.dbl,
            self.scale,
            always=True,
            complete=False,
            short_circuit=True,
        )
        with local(DefaultContext()) as ctx:
            mult.init(self.secp128r1, self.base)
            mult.multiply(scalar)

        lm = HammingDistance()
        trace = []

        def callback(action):
            if isinstance(action, FormulaAction):
                for intermediate in action.op_results:
                    if intermediate.op == OpType.Mult:
                        values = list(map(lambda v: v.value if isinstance(v, OpResult) else v, intermediate.parents))
                        leak = lm(*values)
                        trace.append(leak)

        ctx.actions.walk(callback)
        self.assertGreater(len(trace), 0)
