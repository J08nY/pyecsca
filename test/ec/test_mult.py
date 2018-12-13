from unittest import TestCase

from pyecsca.ec.context import Context
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import RTLMultiplier
from pyecsca.ec.point import Point


class ScalarMultiplierTests(TestCase):

    def test_rtl_simple(self):
        p = 11
        coords = ShortWeierstrassModel.coordinates["projective"]
        curve = EllipticCurve(ShortWeierstrassModel, coords, dict(a=5, b=7),
                              Point(coords, X=Mod(0, p), Y=Mod(0, p), Z=Mod(1, p)))
        with Context() as ctx:
            mult = RTLMultiplier(curve, coords.formulas["add-2002-bj"],
                                 coords.formulas["dbl-2007-bl"], ctx=ctx)
            result = mult.multiply(10, Point(coords, X=Mod(4, p), Y=Mod(3, p), Z=Mod(1, p)))
            print(ctx.intermediates)
