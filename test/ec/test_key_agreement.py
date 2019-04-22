from unittest import TestCase

from pyecsca.ec.key_agreement import *
from pyecsca.ec.mult import LTRMultiplier
from .curves import get_secp128r1


class KeyAgreementTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mult = LTRMultiplier(self.secp128r1, self.add, self.dbl)
        self.priv_a = 0xdeadbeef
        self.pub_a = self.mult.multiply(self.priv_a, self.secp128r1.generator)
        self.priv_b = 0xcafebabe
        self.pub_b = self.mult.multiply(self.priv_b, self.secp128r1.generator)
        self.algos = [ECDH_NONE, ECDH_SHA1, ECDH_SHA224, ECDH_SHA256, ECDH_SHA384, ECDH_SHA512]

    def test_all(self):
        for algo in self.algos:
            result_ab = algo(self.mult, self.pub_a, self.priv_b).perform()
            result_ba = algo(self.mult, self.pub_b, self.priv_a).perform()
            self.assertEqual(result_ab, result_ba)
