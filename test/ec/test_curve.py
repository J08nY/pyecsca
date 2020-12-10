from binascii import unhexlify
from unittest import TestCase

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.params import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import MontgomeryModel
from pyecsca.ec.point import Point, InfinityPoint


class CurveTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.affine_base = self.base.to_affine()
        self.curve25519 = get_params("other", "Curve25519", "xz")
        self.ed25519 = get_params("other", "Ed25519", "projective")

    def test_init(self):
        with self.assertRaises(ValueError):
            EllipticCurve(MontgomeryModel(), self.secp128r1.curve.coordinate_model, 1,
                          InfinityPoint(self.secp128r1.curve.coordinate_model), parameters={})

        with self.assertRaises(ValueError):
            EllipticCurve(self.secp128r1.curve.model, self.secp128r1.curve.coordinate_model, 15,
                          InfinityPoint(self.secp128r1.curve.coordinate_model), parameters={"c": 0})

        with self.assertRaises(ValueError):
            EllipticCurve(self.secp128r1.curve.model, self.secp128r1.curve.coordinate_model, 15,
                          InfinityPoint(self.secp128r1.curve.coordinate_model),
                          parameters={"a": Mod(1, 5), "b": Mod(2, 5)})

    def test_is_neutral(self):
        self.assertTrue(self.secp128r1.curve.is_neutral(InfinityPoint(self.secp128r1.curve.coordinate_model)))

    def test_is_on_curve(self):
        self.assertTrue(self.secp128r1.curve.is_on_curve(self.secp128r1.curve.neutral))
        pt = Point(self.secp128r1.curve.coordinate_model,
                   X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                   Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, self.secp128r1.curve.prime),
                   Z=Mod(1, self.secp128r1.curve.prime))
        self.assertTrue(self.secp128r1.curve.is_on_curve(pt))
        self.assertTrue(self.secp128r1.curve.is_on_curve(pt.to_affine()))
        other = Point(self.secp128r1.curve.coordinate_model,
                      X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, self.secp128r1.curve.prime),
                      Y=Mod(0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, self.secp128r1.curve.prime),
                      Z=Mod(1, self.secp128r1.curve.prime))
        self.assertFalse(self.secp128r1.curve.is_on_curve(other))
        self.assertFalse(self.secp128r1.curve.is_on_curve(self.curve25519.generator))

    def test_affine_add(self):
        pt = Point(AffineCoordinateModel(self.secp128r1.curve.model),
                   x=Mod(0xeb916224eda4fb356421773573297c15, self.secp128r1.curve.prime),
                   y=Mod(0xbcdaf32a2c08fd4271228fef35070848, self.secp128r1.curve.prime))
        self.assertIsNotNone(self.secp128r1.curve.affine_add(self.affine_base, pt))

        added = self.secp128r1.curve.affine_add(self.affine_base, self.affine_base)
        doubled = self.secp128r1.curve.affine_double(self.affine_base)
        self.assertEqual(added, doubled)
        self.assertEqual(self.secp128r1.curve.affine_add(self.secp128r1.curve.neutral, pt), pt)
        self.assertEqual(self.secp128r1.curve.affine_add(pt, self.secp128r1.curve.neutral), pt)

    def test_affine_double(self):
        self.assertIsNotNone(self.secp128r1.curve.affine_double(self.affine_base))
        self.assertEqual(self.secp128r1.curve.affine_double(self.secp128r1.curve.neutral), self.secp128r1.curve.neutral)

    def test_affine_negate(self):
        self.assertIsNotNone(self.secp128r1.curve.affine_negate(self.affine_base))
        self.assertEqual(self.secp128r1.curve.affine_negate(self.secp128r1.curve.neutral), self.secp128r1.curve.neutral)
        with self.assertRaises(ValueError):
            self.secp128r1.curve.affine_negate(self.base)
        with self.assertRaises(ValueError):
            self.secp128r1.curve.affine_negate(self.curve25519.generator)

    def test_affine_multiply(self):
        expected = self.affine_base
        expected = self.secp128r1.curve.affine_double(expected)
        expected = self.secp128r1.curve.affine_double(expected)
        expected = self.secp128r1.curve.affine_add(expected, self.affine_base)
        expected = self.secp128r1.curve.affine_double(expected)
        self.assertEqual(self.secp128r1.curve.affine_multiply(self.affine_base, 10), expected)
        self.assertEqual(self.secp128r1.curve.affine_multiply(self.secp128r1.curve.neutral, 10), self.secp128r1.curve.neutral)
        with self.assertRaises(ValueError):
            self.secp128r1.curve.affine_multiply(self.base, 10)
        with self.assertRaises(ValueError):
            self.secp128r1.curve.affine_multiply(self.curve25519.generator, 10)

    def test_affine_neutral(self):
        self.assertIsNone(self.secp128r1.curve.affine_neutral)
        self.assertIsNone(self.curve25519.curve.affine_neutral)
        self.assertIsNotNone(self.ed25519.curve.affine_neutral)

    def test_affine_random(self):
        for params in [self.secp128r1, self.curve25519, self.ed25519]:
            for _ in range(20):
                pt = params.curve.affine_random()
                self.assertIsNotNone(pt)
                self.assertTrue(params.curve.is_on_curve(pt))

    def test_neutral_is_affine(self):
        self.assertFalse(self.secp128r1.curve.neutral_is_affine)
        self.assertFalse(self.curve25519.curve.neutral_is_affine)
        self.assertTrue(self.ed25519.curve.neutral_is_affine)

    def test_eq(self):
        self.assertEqual(self.secp128r1.curve, self.secp128r1.curve)
        self.assertNotEqual(self.secp128r1.curve, self.curve25519.curve)
        self.assertNotEqual(self.secp128r1.curve, None)

    def test_decode(self):
        affine_curve = self.secp128r1.curve.to_affine()
        affine_point = self.secp128r1.generator.to_affine()
        decoded = affine_curve.decode_point(bytes(affine_point))
        self.assertEqual(decoded, affine_point)

        affine_compressed_bytes = unhexlify("03161ff7528b899b2d0c28607ca52c5b86")
        decoded_compressed = affine_curve.decode_point(affine_compressed_bytes)
        self.assertEqual(decoded_compressed, affine_point)
        affine_compressed_bytes = unhexlify("02161ff7528b899b2d0c28607ca52c5b86")
        decoded_compressed = affine_curve.decode_point(affine_compressed_bytes)
        decoded_compressed = self.secp128r1.curve.affine_negate(decoded_compressed)
        self.assertEqual(decoded_compressed, affine_point)

        infinity_bytes = unhexlify("00")
        decoded_infinity = affine_curve.decode_point(infinity_bytes)
        self.assertEqual(affine_curve.neutral, decoded_infinity)

        with self.assertRaises(ValueError):
            affine_curve.decode_point(unhexlify("03161ff7528b899b2d0c28607ca52c5b"))
        with self.assertRaises(ValueError):
            affine_curve.decode_point(unhexlify("04161ff7528b899b2d0c28607ca52c5b2c5b2c5b2c5b"))
        with self.assertRaises(ValueError):
            affine_curve.decode_point(unhexlify("7a161ff7528b899b2d0c28607ca52c5b86"))
        with self.assertRaises(ValueError):
            affine_curve.decode_point(unhexlify("03161ff7528b899b2d0c28607ca52c5b88"))

