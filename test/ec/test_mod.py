from unittest import TestCase

from pyecsca.ec.mod import Mod, gcd, extgcd


class ModTests(TestCase):

    def test_gcd(self):
        self.assertEqual(gcd(15, 20), 5)
        self.assertEqual(extgcd(15, 20), (-1, 1, 5))

    def test_wrong_mod(self):
        a = Mod(5, 7)
        b = Mod(4, 11)
        with self.assertRaises(ValueError):
            a + b

    def test_other(self):
        a = Mod(5, 7)
        b = Mod(3, 7)
        self.assertEqual(int(-a), 2)
        self.assertEqual(str(a), "5")
        self.assertEqual(6 - a, Mod(1, 7))
        self.assertNotEqual(a, b)
        self.assertEqual(a / b, Mod(4, 7))
        self.assertEqual(a // b, Mod(4, 7))
        self.assertEqual(5 / b, Mod(4, 7))
        self.assertEqual(5 // b, Mod(4, 7))
        self.assertEqual(divmod(a, b), (Mod(1, 7), Mod(2, 7)))
        self.assertNotEqual(a, 6)