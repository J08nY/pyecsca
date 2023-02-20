from unittest import TestCase

from pyecsca.ec.mod import Mod
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
