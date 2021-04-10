from unittest import TestCase

from pyecsca.ec.params import get_params
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mult import LTRMultiplier


class KeyGenerationTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mult = LTRMultiplier(self.add, self.dbl)

    def test_basic(self):
        generator = KeyGeneration(self.mult, self.secp128r1)
        priv, pub = generator.generate()
        self.assertIsNotNone(priv)
        self.assertIsNotNone(pub)
        self.assertTrue(self.secp128r1.curve.is_on_curve(pub))
        generator = KeyGeneration(self.mult, self.secp128r1, True)
        priv, pub = generator.generate()
        self.assertIsNotNone(priv)
        self.assertIsNotNone(pub)
        self.assertTrue(self.secp128r1.curve.is_on_curve(pub))
