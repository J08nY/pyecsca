from unittest import TestCase

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import MontgomeryModel, EdwardsModel
from pyecsca.ec.params import get_params
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.point import Point


class RegressionTests(TestCase):
    def test_issue_7(self):
        secp128r1 = get_params("secg", "secp128r1", "projective")
        base = secp128r1.generator
        coords = secp128r1.curve.coordinate_model
        add = coords.formulas["add-1998-cmo"]
        dbl = coords.formulas["dbl-1998-cmo"]
        scl = coords.formulas["z"]
        mult = LTRMultiplier(
            add, dbl, scl, always=False, complete=False, short_circuit=True
        )
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

    def test_issue_9(self):
        model = MontgomeryModel()
        coords = model.coordinates["xz"]
        p = 19
        neutral = Point(coords, X=Mod(1, p), Z=Mod(0, p))
        curve = EllipticCurve(
            model, coords, p, neutral, {"a": Mod(8, p), "b": Mod(1, p)}
        )
        base = Point(coords, X=Mod(12, p), Z=Mod(1, p))
        formula = coords.formulas["dbl-1987-m-2"]
        res = formula(p, base, **curve.parameters)[0]
        self.assertIsNotNone(res)
        affine_base = Point(AffineCoordinateModel(model), x=Mod(12, p), y=Mod(2, p))
        dbase = curve.affine_double(affine_base).to_model(coords, curve)
        ladder = coords.formulas["ladd-1987-m-3"]
        one, other = ladder(p, base, dbase, base, **curve.parameters)
        self.assertIsNotNone(one)
        self.assertIsNotNone(other)

    def test_issue_10(self):
        model = EdwardsModel()
        coords = model.coordinates["yz"]
        coords_sqr = model.coordinates["yzsquared"]
        p = 0x1D
        c = Mod(1, p)
        d = Mod(0x1C, p)
        r = d.sqrt()
        neutral = Point(coords, Y=c * r, Z=Mod(1, p))
        curve = EllipticCurve(model, coords, p, neutral, {"c": c, "d": d, "r": r})
        neutral_affine = Point(AffineCoordinateModel(model), x=Mod(0, p), y=c)
        self.assertEqual(neutral, neutral_affine.to_model(coords, curve))
        neutral_sqr = Point(coords_sqr, Y=c ** 2 * r, Z=Mod(1, p))
        self.assertEqual(neutral_sqr, neutral_affine.to_model(coords_sqr, curve))
