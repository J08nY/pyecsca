from unittest import TestCase

from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point
from test.ec.curves import get_secp128r1


class CurveTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.base = self.secp128r1.generator

    def test_is_on_curve(self):
        pt = Point(self.secp128r1.curve.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.curve.prime),
                   Z=Mod(1, self.secp128r1.curve.prime))
        assert self.secp128r1.curve.is_on_curve(pt)
