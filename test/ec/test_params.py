from unittest import TestCase

from pyecsca.ec.curves import get_params
from pyecsca.ec.point import InfinityPoint


class DomainParameterTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.curve25519 = get_params("other", "Curve25519", "xz")

    def test_is_neutral(self):
        assert self.secp128r1.is_neutral(InfinityPoint(self.secp128r1.curve.coordinate_model))

    def test_eq(self):
        self.assertEqual(self.secp128r1, self.secp128r1)
        self.assertNotEqual(self.secp128r1, self.curve25519)
        self.assertNotEqual(self.secp128r1, None)

    def test_str(self):
        self.assertEqual(str(self.secp128r1), "DomainParameters(secg/secp128r1)")
