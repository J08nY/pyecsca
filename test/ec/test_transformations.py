from unittest import TestCase

from pyecsca.ec.params import get_params
from pyecsca.ec.transformations import M2SW, M2TE


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
