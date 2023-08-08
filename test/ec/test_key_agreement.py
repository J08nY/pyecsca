import pytest
from pyecsca.ec.key_agreement import (
    ECDH_NONE,
    ECDH_SHA1,
    ECDH_SHA224,
    ECDH_SHA256,
    ECDH_SHA384,
    ECDH_SHA512,
)
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier


@pytest.fixture()
def mult(secp128r1):
    add = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    dbl = secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
    return LTRMultiplier(add, dbl)


@pytest.fixture()
def keypair_a(secp128r1, mult):
    priv_a = Mod(0xDEADBEEF, secp128r1.order)
    mult.init(secp128r1, secp128r1.generator)
    pub_a = mult.multiply(int(priv_a))
    return priv_a, pub_a


@pytest.fixture()
def keypair_b(secp128r1, mult):
    priv_b = Mod(0xCAFEBABE, secp128r1.order)
    mult.init(secp128r1, secp128r1.generator)
    pub_b = mult.multiply(int(priv_b))
    return priv_b, pub_b


@pytest.mark.parametrize("algo", [ECDH_NONE, ECDH_SHA1, ECDH_SHA224, ECDH_SHA256, ECDH_SHA384, ECDH_SHA512])
def test_ka(algo, mult, secp128r1, keypair_a, keypair_b):
    result_ab = algo(mult, secp128r1, keypair_a[1], keypair_b[0]).perform()
    result_ba = algo(mult, secp128r1, keypair_b[1], keypair_a[0]).perform()
    assert result_ab == result_ba

# TODO: Add KAT-based tests here.
