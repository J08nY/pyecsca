from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.params import get_params
from pyecsca.ec.key_agreement import (ECDH_NONE, ECDH_SHA1, ECDH_SHA224, ECDH_SHA256, ECDH_SHA384,
                                      ECDH_SHA512)
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier


class KeyAgreementTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mult = LTRMultiplier(self.add, self.dbl)
        self.priv_a = Mod(0xdeadbeef, self.secp128r1.order)
        self.mult.init(self.secp128r1, self.secp128r1.generator)
        self.pub_a = self.mult.multiply(int(self.priv_a))
        self.priv_b = Mod(0xcafebabe, self.secp128r1.order)
        self.pub_b = self.mult.multiply(int(self.priv_b))

    @parameterized.expand([
        ("NONE", ECDH_NONE),
        ("SHA1", ECDH_SHA1),
        ("SHA224", ECDH_SHA224),
        ("SHA256", ECDH_SHA256),
        ("SHA384", ECDH_SHA384),
        ("SHA512", ECDH_SHA512)
    ])
    def test_all(self, name, algo):
        result_ab = algo(self.mult, self.secp128r1, self.pub_a, self.priv_b).perform()
        result_ba = algo(self.mult, self.secp128r1, self.pub_b, self.priv_a).perform()
        self.assertEqual(result_ab, result_ba)

    # TODO: Add KAT-based tests here.
