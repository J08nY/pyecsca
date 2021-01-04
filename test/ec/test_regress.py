from unittest import TestCase

from pyecsca.ec.mod import Mod
from pyecsca.ec.params import get_params
from pyecsca.ec.mult import LTRMultiplier


class RegressionTests(TestCase):

    def test_issue_7(self):
        secp128r1 = get_params("secg", "secp128r1", "projective")
        base = secp128r1.generator
        coords = secp128r1.curve.coordinate_model
        add = coords.formulas["add-1998-cmo"]
        dbl = coords.formulas["dbl-1998-cmo"]
        scl = coords.formulas["z"]
        mult = LTRMultiplier(add, dbl, scl, always=False, complete=False, short_circuit=True)
        mult.init(secp128r1, base)
        pt = mult.multiply(13613624287328732)
        self.assertIsInstance(pt.coords["X"], Mod)
        self.assertIsInstance(pt.coords["Y"], Mod)
        self.assertIsInstance(pt.coords["Z"], Mod)
        mult.init(secp128r1, pt)
        a = mult.multiply(1)
        self.assertNotIsInstance(a.coords["X"].x, float)
        self.assertNotIsInstance(a.coords["Y"].x, float)
        self.assertNotIsInstance(a.coords["Z"].x, float)

    def test_issue_8(self):
        e222 = get_params("other", "E-222", "projective")
        base = e222.generator
        affine_base = base.to_affine()
        affine_double = e222.curve.affine_double(affine_base)
        affine_triple = e222.curve.affine_add(affine_base, affine_double)
        self.assertIsNotNone(affine_double)
        self.assertIsNotNone(affine_triple)
