from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.params import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.signature import (Signature, SignatureResult, ECDSA_NONE, ECDSA_SHA1, ECDSA_SHA224,
                                  ECDSA_SHA256, ECDSA_SHA384, ECDSA_SHA512)


class SignatureTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mult = LTRMultiplier(self.add, self.dbl)
        self.msg = 0xcafebabe.to_bytes(4, byteorder="big")
        self.priv = Mod(0xdeadbeef, self.secp128r1.order)
        self.mult.init(self.secp128r1, self.secp128r1.generator)
        self.pub = self.mult.multiply(self.priv.x)

    @parameterized.expand([
        ("SHA1", ECDSA_SHA1),
        ("SHA224", ECDSA_SHA224),
        ("SHA256", ECDSA_SHA256),
        ("SHA384", ECDSA_SHA384),
        ("SHA512", ECDSA_SHA512)
    ])
    def test_all(self, name, algo):
        signer = algo(self.mult, self.secp128r1, privkey=self.priv)
        self.assertTrue(signer.can_sign)
        sig = signer.sign_data(self.msg)
        verifier = algo(self.mult, self.secp128r1, add=self.add, pubkey=self.pub)
        self.assertTrue(verifier.can_verify)
        self.assertTrue(verifier.verify_data(sig, self.msg))

        none = ECDSA_NONE(self.mult, self.secp128r1, add=self.add, pubkey=self.pub, privkey=self.priv)
        digest = signer.hash_algo(self.msg).digest()
        sig = none.sign_hash(digest)
        self.assertTrue(none.verify_hash(sig, digest))

    def test_cannot(self):
        ok = ECDSA_NONE(self.mult, self.secp128r1, add=self.add, pubkey=self.pub, privkey=self.priv)
        data = b"aaaa"
        sig = ok.sign_data(data)

        no_priv = ECDSA_NONE(self.mult, self.secp128r1, pubkey=self.pub)
        with self.assertRaises(RuntimeError):
            no_priv.sign_data(data)
        with self.assertRaises(RuntimeError):
            no_priv.sign_hash(data)
        no_pubadd = ECDSA_NONE(self.mult, self.secp128r1, privkey=self.priv)
        with self.assertRaises(RuntimeError):
            no_pubadd.verify_data(sig, data)
        with self.assertRaises(RuntimeError):
            no_pubadd.verify_hash(sig, data)

        with self.assertRaises(ValueError):
            Signature(self.mult, self.secp128r1)

    @parameterized.expand([
        ("SHA1", ECDSA_SHA1),
        ("SHA224", ECDSA_SHA224),
        ("SHA256", ECDSA_SHA256),
        ("SHA384", ECDSA_SHA384),
        ("SHA512", ECDSA_SHA512)
    ])
    def test_fixed_nonce(self, name, algo):
        signer = algo(self.mult, self.secp128r1, privkey=self.priv)
        sig_one = signer.sign_data(self.msg, nonce=0xabcdef)
        sig_other = signer.sign_data(self.msg, nonce=0xabcdef)
        verifier = algo(self.mult, self.secp128r1, add=self.add, pubkey=self.pub)
        self.assertTrue(verifier.verify_data(sig_one, self.msg))
        self.assertTrue(verifier.verify_data(sig_other, self.msg))
        self.assertEqual(sig_one, sig_other)

    def test_der(self):
        sig = SignatureResult(0xaaaaa, 0xbbbbb)
        self.assertEqual(sig, SignatureResult.from_DER(sig.to_DER()))
        self.assertNotEqual(sig, "abc")
