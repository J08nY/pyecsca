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
        group = get_params(*name.split("/"), coords)
        try:
            assert group.curve.is_on_curve(group.generator)
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