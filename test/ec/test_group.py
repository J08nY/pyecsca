from unittest import TestCase

from pyecsca.ec.curves import get_curve
from pyecsca.ec.point import InfinityPoint


class AbelianGroupTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_curve("secp128r1", "projective")
        self.curve25519 = get_curve("curve25519", "xz")

    def test_is_neutral(self):
        assert self.secp128r1.is_neutral(InfinityPoint(self.secp128r1.curve.coordinate_model))

    def test_eq(self):
        self.assertEqual(self.secp128r1, self.secp128r1)
        self.assertNotEqual(self.secp128r1, self.curve25519)
        self.assertNotEqual(self.secp128r1, None)
