from unittest import TestCase

from hashlib import sha1
from pyecsca.ec.signature import *
from pyecsca.ec.mult import LTRMultiplier
from .curves import get_secp128r1


class SignatureTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mult = LTRMultiplier(self.secp128r1, self.add, self.dbl)
        self.msg = 0xcafebabe.to_bytes(4, byteorder="big")
        self.priv = 0xdeadbeef
        self.pub = self.mult.multiply(self.priv, self.secp128r1.generator)
        self.algos = [ECDSA_SHA1, ECDSA_SHA224, ECDSA_SHA256, ECDSA_SHA384, ECDSA_SHA512]

    def test_all(self):
        for algo in self.algos:
            signer = algo(self.mult, privkey=self.priv)
            assert signer.can_sign
            sig = signer.sign_data(self.msg)
            verifier = algo(self.mult, add=self.add, pubkey=self.pub)
            assert verifier.can_verify
            assert verifier.verify_data(sig, self.msg)
        none = ECDSA_NONE(self.mult, add=self.add, pubkey=self.pub, privkey=self.priv)
        digest = sha1(self.msg).digest()
        sig = none.sign_hash(digest)
        assert none.verify_hash(sig, digest)
        sig = none.sign_data(digest)
        assert none.verify_data(sig, digest)

    def test_fixed_nonce(self):
        for algo in self.algos:
            signer = algo(self.mult, privkey=self.priv)
            sig_one = signer.sign_data(self.msg, nonce=0xabcdef)
            sig_other = signer.sign_data(self.msg, nonce=0xabcdef)
            verifier = algo(self.mult, add=self.add, pubkey=self.pub)
            assert verifier.verify_data(sig_one, self.msg)
            assert verifier.verify_data(sig_other, self.msg)
            self.assertEqual(sig_one, sig_other)

    def test_der(self):
        sig = SignatureResult(0xaaaaa, 0xbbbbb)
        self.assertEqual(sig, SignatureResult.from_DER(sig.to_DER()))
