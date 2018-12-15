from unittest import TestCase

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.mult import LTRMultiplier, RTLMultiplier, LadderMultiplier
from pyecsca.ec.point import Point


class ScalarMultiplierTests(TestCase):

    def setUp(self):
        self.p = 0xfffffffdffffffffffffffffffffffff
        self.coords = ShortWeierstrassModel.coordinates["projective"]
        self.base = Point(self.coords, X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.p),
                          Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.p),
                          Z=Mod(1, self.p))
        self.secp128r1 = EllipticCurve(ShortWeierstrassModel, self.coords,
                                       dict(a=0xfffffffdfffffffffffffffffffffffc,
                                            b=0xe87579c11079f43dd824993c2cee5ed3),
                                       Point(self.coords, X=Mod(0, self.p), Y=Mod(1, self.p),
                                             Z=Mod(0, self.p)))

        self.coords25519 = MontgomeryModel.coordinates["xz"]
        self.p25519 = 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffed
        self.base25519 = Point(self.coords25519, X=Mod(9, self.p25519),
                               Z=Mod(1, self.p25519))
        self.curve25519 = EllipticCurve(MontgomeryModel, self.coords25519,
                                        dict(a=486662, b=1),
                                        Point(self.coords25519,
                                              X=Mod(0, self.p25519), Z=Mod(1, self.p25519)))

    def test_rtl_simple(self):
        mult = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)

    def test_ltr_simple(self):
        mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)

    def test_ladder_simple(self):
        mult = LadderMultiplier(self.curve25519, self.coords25519.formulas["ladd-1987-m"],
                                self.coords25519.formulas["scale"])
        res = mult.multiply(15, self.base25519)
        other = mult.multiply(3, self.base25519)
        other = mult.multiply(5, other)
        self.assertEqual(res, other)

    def test_basic_multipliers(self):
        ltr = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_ltr = ltr.multiply(10, self.base)
        rtl = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_rtl = rtl.multiply(10, self.base)
        self.assertEqual(res_ltr, res_rtl)
