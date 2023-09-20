import json

import pytest
from importlib_resources import files
import test.data.ec
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import get_params
from pyecsca.ec.point import Point
from pyecsca.ec.signature import (
    Signature,
    SignatureResult,
    ECDSA_NONE,
    ECDSA_SHA1,
    ECDSA_SHA224,
    ECDSA_SHA256,
    ECDSA_SHA384,
    ECDSA_SHA512,
)


@pytest.fixture()
def add(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["add-2007-bl"]


@pytest.fixture()
def mult(secp128r1, add):
    dbl = secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
    return LTRMultiplier(add, dbl)


@pytest.fixture()
def keypair(secp128r1, mult):
    priv = Mod(0xDEADBEEF, secp128r1.order)
    mult.init(secp128r1, secp128r1.generator)
    pub = mult.multiply(int(priv))
    return priv, pub


@pytest.fixture()
def msg():
    return 0xCAFEBABE.to_bytes(4, byteorder="big")


@pytest.mark.parametrize("algo",
                         [
                             ECDSA_SHA1,
                             ECDSA_SHA224,
                             ECDSA_SHA256,
                             ECDSA_SHA384,
                             ECDSA_SHA512,
                         ])
def test_all(secp128r1, mult, keypair, msg, add, algo):
    priv, pub = keypair
    signer = algo(mult, secp128r1, privkey=keypair[0])
    assert signer.can_sign
    sig = signer.sign_data(msg)
    verifier = algo(mult, secp128r1, add=add, pubkey=pub)
    assert verifier.can_verify
    assert verifier.verify_data(sig, msg)

    none = ECDSA_NONE(
        mult, secp128r1, add=add, pubkey=pub, privkey=priv
    )
    digest = signer.hash_algo(msg).digest()
    sig = none.sign_hash(digest)
    assert none.verify_hash(sig, digest)


def test_cannot(secp128r1, add, mult, keypair):
    priv, pub = keypair
    ok = ECDSA_NONE(
        mult, secp128r1, add=add, pubkey=pub, privkey=priv
    )
    data = b"aaaa"
    sig = ok.sign_data(data)

    no_priv = ECDSA_NONE(mult, secp128r1, pubkey=pub)
    with pytest.raises(RuntimeError):
        no_priv.sign_data(data)
    with pytest.raises(RuntimeError):
        no_priv.sign_hash(data)
    no_pubadd = ECDSA_NONE(mult, secp128r1, privkey=priv)
    with pytest.raises(RuntimeError):
        no_pubadd.verify_data(sig, data)
    with pytest.raises(RuntimeError):
        no_pubadd.verify_hash(sig, data)

    with pytest.raises(ValueError):
        Signature(mult, secp128r1)


@pytest.mark.parametrize("algo",
                         [
                             ECDSA_SHA1,
                             ECDSA_SHA224,
                             ECDSA_SHA256,
                             ECDSA_SHA384,
                             ECDSA_SHA512,
                         ])
def test_fixed_nonce(secp128r1, mult, keypair, msg, add, algo):
    priv, pub = keypair
    signer = algo(mult, secp128r1, privkey=priv)
    sig_one = signer.sign_data(msg, nonce=0xABCDEF)
    sig_other = signer.sign_data(msg, nonce=0xABCDEF)
    verifier = algo(mult, secp128r1, add=add, pubkey=pub)
    assert verifier.verify_data(sig_one, msg)
    assert verifier.verify_data(sig_other, msg)
    assert sig_one == sig_other


def test_der():
    sig = SignatureResult(0xAAAAA, 0xBBBBB)
    assert sig == SignatureResult.from_DER(sig.to_DER())
    assert sig != "abc"


def test_ecdsa_nist():
    with files(test.data.ec).joinpath("ecdsa_tv.json").open("r") as f:
        nist_data = json.load(f)

    P192 = get_params("nist", "P-192", "projective")
    affine_model = AffineCoordinateModel(P192.curve.model)
    add = P192.curve.coordinate_model.formulas["add-2015-rcb"]
    dbl = P192.curve.coordinate_model.formulas["dbl-2015-rcb"]
    mult = LTRMultiplier(add, dbl)
    priv = Mod(int(nist_data["priv"], 16), P192.order)

    pub_affine = Point(affine_model,
                       x=Mod(int(nist_data["pub"]["x"], 16), P192.curve.prime),
                       y=Mod(int(nist_data["pub"]["y"], 16), P192.curve.prime))
    pub = pub_affine.to_model(P192.curve.coordinate_model, P192.curve)

    signer = ECDSA_SHA1(mult, P192, add, pub, priv)

    nonce = int(nist_data["k"], 16)
    data = bytes.fromhex(nist_data["msg"])
    signature = signer.sign_hash(data, nonce=nonce)
    assert signature.r == int(nist_data["signature"]["r"], 16)
    assert signature.s == int(nist_data["signature"]["s"], 16)
    assert signer.verify_hash(signature, data)
