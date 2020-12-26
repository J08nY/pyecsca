from unittest import TestCase

from pyecsca.ec.mod import Mod, gcd, extgcd, Undefined, miller_rabin, has_gmp, RawMod
from pyecsca.ec.error import NonInvertibleError, NonResidueError, NonInvertibleWarning, NonResidueWarning
from pyecsca.misc.cfg import getconfig, TemporaryConfig


class ModTests(TestCase):

    def test_gcd(self):
        self.assertEqual(gcd(15, 20), 5)
        self.assertEqual(extgcd(15, 0), (1, 0, 15))
        self.assertEqual(extgcd(15, 20), (-1, 1, 5))

    def test_miller_rabin(self):
        self.assertTrue(miller_rabin(2))
        self.assertTrue(miller_rabin(3))
        self.assertTrue(miller_rabin(5))
        self.assertFalse(miller_rabin(8))
        self.assertTrue(miller_rabin(0xe807561107ccf8fa82af74fd492543a918ca2e9c13750233a9))
        self.assertFalse(miller_rabin(0x6f6889deb08da211927370810f026eb4c17b17755f72ea005))

    def test_inverse(self):
        p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
        self.assertEqual(Mod(0x702bdafd3c1c837b23a1cb196ed7f9fadb333c5cfe4a462be32adcd67bfb6ac1, p).inverse(), Mod(0x1cb2e5274bba085c4ca88eede75ae77949e7a410c80368376e97ab22eb590f9d, p))
        with self.assertRaises(NonInvertibleError):
            Mod(0, p).inverse()
        with self.assertRaises(NonInvertibleError):
            Mod(5, 10).inverse()
        getconfig().ec.no_inverse_action = "warning"
        with self.assertRaises(NonInvertibleWarning):
            Mod(0, p).inverse()
        with self.assertRaises(NonInvertibleWarning):
            Mod(5, 10).inverse()
        getconfig().ec.no_inverse_action = "ignore"
        Mod(0, p).inverse()
        Mod(5, 10).inverse()
        getconfig().ec.no_inverse_action = "error"

    def test_is_residue(self):
        self.assertTrue(Mod(4, 11).is_residue())
        self.assertFalse(Mod(11, 31).is_residue())
        self.assertTrue(Mod(0, 7).is_residue())
        self.assertTrue(Mod(1, 2).is_residue())

    def test_sqrt(self):
        p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
        self.assertIn(Mod(0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc, p).sqrt(), (0x9add512515b70d9ec471151c1dec46625cd18b37bde7ca7fb2c8b31d7033599d, 0x6522aed9ea48f2623b8eeae3e213b99da32e74c9421835804d374ce28fcca662))
        with self.assertRaises(NonResidueError):
            Mod(0x702bdafd3c1c837b23a1cb196ed7f9fadb333c5cfe4a462be32adcd67bfb6ac1, p).sqrt()
        getconfig().ec.non_residue_action = "warning"
        with self.assertRaises(NonResidueWarning):
            Mod(0x702bdafd3c1c837b23a1cb196ed7f9fadb333c5cfe4a462be32adcd67bfb6ac1, p).sqrt()
        getconfig().ec.non_residue_action = "ignore"
        Mod(0x702bdafd3c1c837b23a1cb196ed7f9fadb333c5cfe4a462be32adcd67bfb6ac1, p).sqrt()
        with TemporaryConfig() as cfg:
            cfg.ec.non_residue_action = "warning"
            with self.assertRaises(NonResidueWarning):
                Mod(0x702bdafd3c1c837b23a1cb196ed7f9fadb333c5cfe4a462be32adcd67bfb6ac1, p).sqrt()
        self.assertEqual(Mod(0, p).sqrt(), Mod(0, p))
        q = 0x75d44fee9a71841ae8403c0c251fbad
        self.assertIn(Mod(0x591e0db18cf1bd81a11b2985a821eb3, q).sqrt(), (0x113b41a1a2b73f636e73be3f9a3716e, 0x64990e4cf7ba44b779cc7dcc8ae8a3f))
        getconfig().ec.non_residue_action = "error"

    def test_eq(self):
        self.assertEqual(Mod(1, 7), 1)
        self.assertNotEqual(Mod(1, 7), "1")
        self.assertEqual(Mod(1, 7), Mod(1, 7))
        self.assertNotEqual(Mod(1, 7), Mod(5, 7))
        self.assertNotEqual(Mod(1, 7), Mod(1, 5))

    def test_pow(self):
        a = Mod(5, 7)
        self.assertEqual(a**(-1), a.inverse())
        self.assertEqual(a**0, Mod(1, 7))
        self.assertEqual(a**(-2),a.inverse()**2)

    def test_wrong_mod(self):
        a = Mod(5, 7)
        b = Mod(4, 11)
        with self.assertRaises(ValueError):
            a + b

    def test_wrong_pow(self):
        a = Mod(5, 7)
        c = Mod(4, 11)
        with self.assertRaises(TypeError):
            a**c

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
        self.assertEqual(a / 3, Mod(4, 7))
        self.assertEqual(a // 3, Mod(4, 7))
        self.assertEqual(divmod(a, b), (Mod(1, 7), Mod(2, 7)))
        self.assertEqual(a + b, Mod(1, 7))
        self.assertEqual(5 + b, Mod(1, 7))
        self.assertEqual(a + 3, Mod(1, 7))
        self.assertNotEqual(a, 6)

    def test_undefined(self):
        u = Undefined()
        for k, meth in u.__class__.__dict__.items():
            if k in ("__module__", "__new__", "__init__", "__doc__", "__hash__", "__abstractmethods__", "_abc_impl"):
                continue
            args = [5 for _ in range(meth.__code__.co_argcount - 1)]
            if k == "__repr__":
                self.assertEqual(meth(u), "Undefined")
            elif k in ("__eq__", "__ne__"):
                assert not meth(u, *args)
            else:
                with self.assertRaises(NotImplementedError):
                    meth(u, *args)

    def test_implementation(self):
        if not has_gmp:
            self.skipTest("Only makes sense if more Mod implementations are available.")
        with TemporaryConfig() as cfg:
            cfg.ec.mod_implementation = "python"
            self.assertIsInstance(Mod(5, 7), RawMod)
