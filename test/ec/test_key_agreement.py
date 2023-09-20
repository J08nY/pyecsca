from copy import copy

import pytest
import json
from importlib_resources import files

from pyecsca.ec.coordinates import AffineCoordinateModel
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
import test.data.ec
from pyecsca.ec.params import get_params
from pyecsca.ec.point import Point


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


def test_ka_secg():
    with files(test.data.ec).joinpath("ecdh_tv.json").open("r") as f:
        secg_data = json.load(f)
    secp160r1 = get_params("secg", "secp160r1", "projective")
    affine_model = AffineCoordinateModel(secp160r1.curve.model)
    add = secp160r1.curve.coordinate_model.formulas["add-2015-rcb"]
    dbl = secp160r1.curve.coordinate_model.formulas["dbl-2015-rcb"]
    mult = LTRMultiplier(add, dbl)
    privA = Mod(int(secg_data["keyA"]["priv"], 16), secp160r1.order)
    pubA_affine = Point(affine_model,
                        x=Mod(int(secg_data["keyA"]["pub"]["x"], 16), secp160r1.curve.prime),
                        y=Mod(int(secg_data["keyA"]["pub"]["y"], 16), secp160r1.curve.prime))
    pubA = pubA_affine.to_model(secp160r1.curve.coordinate_model, secp160r1.curve)
    privB = Mod(int(secg_data["keyB"]["priv"], 16), secp160r1.order)
    pubB_affine = Point(affine_model,
                        x=Mod(int(secg_data["keyB"]["pub"]["x"], 16), secp160r1.curve.prime),
                        y=Mod(int(secg_data["keyB"]["pub"]["y"], 16), secp160r1.curve.prime))
    pubB = pubB_affine.to_model(secp160r1.curve.coordinate_model, secp160r1.curve)

    algoAB = ECDH_SHA1(copy(mult), secp160r1, pubA, privB)
    resAB = algoAB.perform()
    algoBA = ECDH_SHA1(copy(mult), secp160r1, pubB, privA)
    resBA = algoBA.perform()

    assert resAB == resBA
    assert resAB == bytes.fromhex(secg_data["sha1"])

    resAB_raw = algoAB.perform_raw()
    x = int(resAB_raw.x)
    p = secp160r1.curve.prime
    n = (p.bit_length() + 7) // 8
    result = x.to_bytes(n, byteorder="big")
    assert result == bytes.fromhex(secg_data["raw"])
