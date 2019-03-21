from unittest import TestCase

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.point import Point, InfinityPoint


class CoordinateTests(TestCase):

    def setUp(self):
        self.p = 0xfffffffdffffffffffffffffffffffff
        self.coords = ShortWeierstrassModel().coordinates["projective"]
        self.secp128r1 = EllipticCurve(ShortWeierstrassModel(), self.coords, self.p,
                                       dict(a=0xfffffffdfffffffffffffffffffffffc,
                                            b=0xe87579c11079f43dd824993c2cee5ed3),
                                       InfinityPoint(self.coords))

    def test_affine(self):
        pt = Point(self.coords, X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.p),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.p),
                   Z=Mod(1, self.p))
        affine_Point = pt.to_affine()
        assert pt.equals(affine_Point)
