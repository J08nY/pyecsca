from unittest import TestCase

from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point, InfinityPoint
from test.ec.curves import get_secp128r1


class CurveTests(TestCase):
    def setUp(self):
        self.secp128r1, self.base = get_secp128r1()

    def test_is_on_curve(self):
        pt = Point(self.secp128r1.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.prime),
                   Z=Mod(1, self.secp128r1.prime))
        assert self.secp128r1.is_on_curve(pt)

    def test_is_neutral(self):
        assert self.secp128r1.is_neutral(InfinityPoint(self.secp128r1.coordinate_model))
