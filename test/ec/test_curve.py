from unittest import TestCase

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import MontgomeryModel
from pyecsca.ec.point import Point
from .curves import get_secp128r1, get_curve25519


class CurveTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.base = self.secp128r1.generator
        self.curve25519 = get_curve25519()

    def test_init(self):
        with self.assertRaises(ValueError):
            EllipticCurve(MontgomeryModel(), self.secp128r1.curve.coordinate_model, 1,
                          parameters={})

        with self.assertRaises(ValueError):
            EllipticCurve(self.secp128r1.curve.model, self.secp128r1.curve.coordinate_model, 15,
                          parameters={"c": 0})

        with self.assertRaises(ValueError):
            EllipticCurve(self.secp128r1.curve.model, self.secp128r1.curve.coordinate_model, 15,
                          parameters={"a": Mod(1, 5), "b": Mod(2, 5)})

    def test_is_on_curve(self):
        pt = Point(self.secp128r1.curve.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.curve.prime),
                   Z=Mod(1, self.secp128r1.curve.prime))
        assert self.secp128r1.curve.is_on_curve(pt)
        assert self.secp128r1.curve.is_on_curve(pt.to_affine())
        other = Point(self.secp128r1.curve.coordinate_model,
                      X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                      Y=Mod(0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, self.secp128r1.curve.prime),
                      Z=Mod(1, self.secp128r1.curve.prime))
        assert not self.secp128r1.curve.is_on_curve(other)

    def test_eq(self):
        self.assertEqual(self.secp128r1.curve, self.secp128r1.curve)
        self.assertNotEqual(self.secp128r1.curve, self.curve25519.curve)

    def test_repr(self):
        self.assertEqual(repr(self.secp128r1.curve),
                         "EllipticCurve([a=340282366762482138434845932244680310780, b=308990863222245658030922601041482374867] on ShortWeierstrassModel() using EFDCoordinateModel(\"projective\" on short Weierstrass curves))")