from unittest import TestCase

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier
from pyecsca.ec.point import Point


class ScalarMultiplierTests(TestCase):

    def setUp(self):
        self.p = 0xfffffffdffffffffffffffffffffffff
        self.coords = ShortWeierstrassModel.coordinates["projective"]
        self.secp128r1 = EllipticCurve(ShortWeierstrassModel, self.coords,
                                       dict(a=0xfffffffdfffffffffffffffffffffffc,
                                            b=0xe87579c11079f43dd824993c2cee5ed3),
                                       Point(self.coords, X=Mod(0, self.p), Y=Mod(1, self.p),
                                             Z=Mod(0, self.p)))
        self.base = Point(self.coords, X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.p),
                          Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.p),
                          Z=Mod(1, self.p))

    def test_rtl_simple(self):
        mult = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        mult.multiply(10, self.base)

    def test_ltr_simple(self):
        mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        mult.multiply(10, self.base)

    def test_basic_multipliers(self):
        ltr = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_ltr = ltr.multiply(10, self.base)
        rtl = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_rtl = rtl.multiply(10, self.base)
        self.assertEqual(res_ltr, res_rtl)
