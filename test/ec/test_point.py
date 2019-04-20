from unittest import TestCase

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.point import Point, InfinityPoint
from test.ec.curves import get_secp128r1


class PointTests(TestCase):
    def setUp(self):
        self.secp128r1, self.base = get_secp128r1()
        self.affine = AffineCoordinateModel(ShortWeierstrassModel())

    def test_to_affine(self):
        pt = Point(self.secp128r1.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.prime),
                   Z=Mod(1, self.secp128r1.prime))
        affine = pt.to_affine()

        self.assertIsInstance(affine.coordinate_model, AffineCoordinateModel)
        self.assertSetEqual(set(affine.coords.keys()), set(self.affine.variables))
        self.assertEqual(affine.coords["x"], pt.coords["X"])
        self.assertEqual(affine.coords["y"], pt.coords["Y"])

        affine = InfinityPoint(self.secp128r1.coordinate_model).to_affine()
        self.assertIsInstance(affine, InfinityPoint)

    def test_from_affine(self):
        affine = Point(self.affine, x=Mod(0xabcd, self.secp128r1.prime),
                       y=Mod(0xef, self.secp128r1.prime))
        projective_model = self.secp128r1.coordinate_model
        other = Point.from_affine(projective_model, affine)

        self.assertEqual(other.coordinate_model, projective_model)
        self.assertSetEqual(set(other.coords.keys()), set(projective_model.variables))
        self.assertEqual(other.coords["X"], affine.coords["x"])
        self.assertEqual(other.coords["Y"], affine.coords["y"])
        self.assertEqual(other.coords["Z"], Mod(1, self.secp128r1.prime))

    def test_to_from_affine(self):
        pt = Point(self.secp128r1.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.prime),
                   Z=Mod(1, self.secp128r1.prime))
        other = Point.from_affine(self.secp128r1.coordinate_model, pt.to_affine())
        self.assertEqual(pt, other)

    def test_equals(self):
        pt = Point(self.secp128r1.coordinate_model,
                   X=Mod(0x4, self.secp128r1.prime),
                   Y=Mod(0x6, self.secp128r1.prime),
                   Z=Mod(2, self.secp128r1.prime))
        other = Point(self.secp128r1.coordinate_model,
                      X=Mod(0x2, self.secp128r1.prime),
                      Y=Mod(0x3, self.secp128r1.prime),
                      Z=Mod(1, self.secp128r1.prime))
        assert pt.equals(other)
