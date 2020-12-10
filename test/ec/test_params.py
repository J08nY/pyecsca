from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.params import get_params, load_params


class DomainParameterTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.curve25519 = get_params("other", "Curve25519", "xz")

    def test_eq(self):
        self.assertEqual(self.secp128r1, self.secp128r1)
        self.assertNotEqual(self.secp128r1, self.curve25519)
        self.assertNotEqual(self.secp128r1, None)

    def test_str(self):
        self.assertEqual(str(self.secp128r1), "DomainParameters(secg/secp128r1)")

    @parameterized.expand([
        ("secg/secp128r1", "projective"),
        ("secg/secp256r1", "projective"),
        ("secg/secp521r1", "projective"),
        ("other/Curve25519", "xz"),
        ("other/Ed25519", "projective"),
        ("other/Ed448", "projective"),
        ("other/E-222", "projective")
    ])
    def test_get_params(self, name, coords):
        params = get_params(*name.split("/"), coords)
        try:
            assert params.curve.is_on_curve(params.generator)
        except NotImplementedError:
            pass

    def test_load_params(self):
        params = load_params("test/data/curve.json", "projective")
        try:
            assert params.curve.is_on_curve(params.generator)
        except NotImplementedError:
            pass

    @parameterized.expand([
        ("no_category/some", "else"),
        ("secg/no_curve", "else"),
        ("secg/secp128r1", "some")
    ])
    def test_unknown(self, name, coords):
        with self.assertRaises(ValueError):
            get_params(*name.split("/"), coords)

    def test_assumption(self):
        with self.assertRaises(ValueError):
            get_params("secg", "secp128r1", "projective-1")
        self.assertIsNotNone(get_params("secg", "secp128r1", "projective-3"))

    def test_infty(self):
        with self.assertRaises(ValueError):
            get_params("other", "Ed25519", "modified", False)
        self.assertIsNotNone(get_params("secg", "secp128r1", "projective", False))

    def test_no_binary(self):
        with self.assertRaises(ValueError):
            get_params("secg", "sect163r1", "something")

    def test_no_extension(self):
        with self.assertRaises(ValueError):
            get_params("other", "Fp254n2BNa", "something")

    def test_affine(self):
        aff = get_params("secg", "secp128r1", "affine")
        self.assertIsInstance(aff.curve.coordinate_model, AffineCoordinateModel)
