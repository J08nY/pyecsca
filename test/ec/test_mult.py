from unittest import TestCase

from pyecsca.ec.context import Context
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import RTLMultiplier
from pyecsca.ec.point import Point


class ScalarMultiplierTests(TestCase):

    def test_rtl_simple(self):
        p = 0xfffffffdffffffffffffffffffffffff
        coords = ShortWeierstrassModel.coordinates["projective"]
        curve = EllipticCurve(ShortWeierstrassModel, coords,
                              dict(a=0xfffffffdfffffffffffffffffffffffc,
                                   b=0xe87579c11079f43dd824993c2cee5ed3),
                              Point(coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p)))
        with Context() as ctx:
            mult = RTLMultiplier(curve, coords.formulas["add-1998-cmo"],
                                 coords.formulas["dbl-1998-cmo"], coords.formulas["z"], ctx=ctx)
            mult.multiply(10, Point(coords, X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, p),
                                    Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, p),
                                    Z=Mod(1, p)))
