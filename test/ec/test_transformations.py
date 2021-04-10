from unittest import TestCase

from pyecsca.ec.params import get_params
from pyecsca.ec.transformations import M2SW, M2TE, TE2M, SW2M, SW2TE


class TransformationTests(TestCase):
    def test_montgomery(self):
        curve25519 = get_params("other", "Curve25519", "affine")
        sw = M2SW(curve25519)
        self.assertIsNotNone(sw)
        self.assertTrue(sw.curve.is_on_curve(sw.generator))
        self.assertTrue(sw.curve.is_neutral(sw.curve.neutral))
        te = M2TE(curve25519)
        self.assertIsNotNone(te)
        self.assertTrue(te.curve.is_on_curve(te.generator))
        self.assertTrue(te.curve.is_neutral(te.curve.neutral))

    def test_twistededwards(self):
        ed25519 = get_params("other", "Ed25519", "affine")
        m = TE2M(ed25519)
        self.assertIsNotNone(m)
        self.assertTrue(m.curve.is_on_curve(m.generator))
        self.assertTrue(m.curve.is_neutral(m.curve.neutral))

    def test_shortweierstrass(self):
        secp128r2 = get_params("secg", "secp128r2", "affine")
        m = SW2M(secp128r2)
        self.assertIsNotNone(m)
        self.assertTrue(m.curve.is_on_curve(m.generator))
        self.assertTrue(m.curve.is_neutral(m.curve.neutral))
        te = SW2TE(secp128r2)
        self.assertIsNotNone(te)
        self.assertTrue(te.curve.is_on_curve(te.generator))
        self.assertTrue(te.curve.is_neutral(te.curve.neutral))
