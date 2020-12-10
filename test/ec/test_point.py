from unittest import TestCase

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.params import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.point import Point, InfinityPoint


class PointTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.affine = AffineCoordinateModel(ShortWeierstrassModel())

    def test_construction(self):
        with self.assertRaises(ValueError):
            Point(self.coords)

    def test_to_affine(self):
        pt = Point(self.coords,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.curve.prime),
                   Z=Mod(1, self.secp128r1.curve.prime))
        affine = pt.to_affine()

        self.assertIsInstance(affine.coordinate_model, AffineCoordinateModel)
        self.assertSetEqual(set(affine.coords.keys()), set(self.affine.variables))
        self.assertEqual(affine.coords["x"], pt.coords["X"])
        self.assertEqual(affine.coords["y"], pt.coords["Y"])
        self.assertEqual(affine.to_affine(), affine)

        affine = InfinityPoint(self.coords).to_affine()
        self.assertIsInstance(affine, InfinityPoint)

    def test_to_model(self):
        affine = Point(self.affine, x=Mod(0xabcd, self.secp128r1.curve.prime),
                       y=Mod(0xef, self.secp128r1.curve.prime))
        projective_model = self.coords
        other = affine.to_model(projective_model, self.secp128r1.curve)

        self.assertEqual(other.coordinate_model, projective_model)
        self.assertSetEqual(set(other.coords.keys()), set(projective_model.variables))
        self.assertEqual(other.coords["X"], affine.coords["x"])
        self.assertEqual(other.coords["Y"], affine.coords["y"])
        self.assertEqual(other.coords["Z"], Mod(1, self.secp128r1.curve.prime))

        infty = InfinityPoint(AffineCoordinateModel(self.secp128r1.curve.model))
        other_infty = infty.to_model(self.coords, self.secp128r1.curve)
        self.assertIsInstance(other_infty, InfinityPoint)
        
        with self.assertRaises(ValueError):
            self.base.to_model(self.coords, self.secp128r1.curve)

    def test_to_from_affine(self):
        pt = Point(self.coords,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.curve.prime),
                   Z=Mod(1, self.secp128r1.curve.prime))
        other = pt.to_affine().to_model(self.coords, self.secp128r1.curve)
        self.assertEqual(pt, other)

    def test_equals(self):
        pt = Point(self.coords,
                   X=Mod(0x4, self.secp128r1.curve.prime),
                   Y=Mod(0x6, self.secp128r1.curve.prime),
                   Z=Mod(2, self.secp128r1.curve.prime))
        other = Point(self.coords,
                      X=Mod(0x2, self.secp128r1.curve.prime),
                      Y=Mod(0x3, self.secp128r1.curve.prime),
                      Z=Mod(1, self.secp128r1.curve.prime))
        third = Point(self.coords,
                      X=Mod(0x5, self.secp128r1.curve.prime),
                      Y=Mod(0x3, self.secp128r1.curve.prime),
                      Z=Mod(1, self.secp128r1.curve.prime))
        self.assertTrue(pt.equals(other))
        self.assertNotEqual(pt, other)
        self.assertFalse(pt.equals(2))
        self.assertNotEqual(pt, 2)
        self.assertFalse(pt.equals(third))
        self.assertNotEqual(pt, third)

        infty_one = InfinityPoint(self.coords)
        infty_other = InfinityPoint(self.coords)
        self.assertTrue(infty_one.equals(infty_other))
        self.assertEqual(infty_one, infty_other)

        mont = MontgomeryModel()
        different = Point(mont.coordinates["xz"],
                          X=Mod(0x64daccd2656420216545e5f65221eb,
                                0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa),
                          Z=Mod(1, 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa))
        self.assertFalse(pt.equals(different))
        self.assertNotEqual(pt, different)

    def test_bytes(self):
        pt = Point(self.coords,
                   X=Mod(0x4, self.secp128r1.curve.prime),
                   Y=Mod(0x6, self.secp128r1.curve.prime),
                   Z=Mod(2, self.secp128r1.curve.prime))
        self.assertEqual(bytes(pt), b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02")
        self.assertEqual(bytes(InfinityPoint(self.coords)), b"\x00")