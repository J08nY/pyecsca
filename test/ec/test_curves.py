from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.curves import get_params


class CurvesTests(TestCase):

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
            get_params("secg", "secp128r1", "modified", False)
        self.assertIsNotNone(get_params("secg", "secp128r1", "projective", False))

    def test_no_binary(self):
        with self.assertRaises(ValueError):
            get_params("secg", "sect163r1", "something")