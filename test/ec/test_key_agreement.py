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
    X25519,
    X448,
)
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.mult import (
    LTRMultiplier,
    LadderMultiplier,
    DifferentialLadderMultiplier,
)
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
    priv_a = mod(0xDEADBEEF, secp128r1.order)
    mult.init(secp128r1, secp128r1.generator)
    pub_a = mult.multiply(int(priv_a))
    return priv_a, pub_a


@pytest.fixture()
def keypair_b(secp128r1, mult):
    priv_b = mod(0xCAFEBABE, secp128r1.order)
    mult.init(secp128r1, secp128r1.generator)
    pub_b = mult.multiply(int(priv_b))
    return priv_b, pub_b


@pytest.mark.parametrize(
    "algo", [ECDH_NONE, ECDH_SHA1, ECDH_SHA224, ECDH_SHA256, ECDH_SHA384, ECDH_SHA512]
)
def test_ka(algo, mult, secp128r1, keypair_a, keypair_b):
    result_ab = algo(mult, secp128r1, keypair_a[1], keypair_b[0]).perform()
    result_ba = algo(mult, secp128r1, keypair_b[1], keypair_a[0]).perform()
    assert result_ab == result_ba


def test_ecdh_secg():
    with files(test.data.ec).joinpath("ecdh_tv.json").open("r") as f:
        secg_data = json.load(f)
    secp160r1 = get_params("secg", "secp160r1", "projective")
    affine_model = AffineCoordinateModel(secp160r1.curve.model)
    add = secp160r1.curve.coordinate_model.formulas["add-2015-rcb"]
    dbl = secp160r1.curve.coordinate_model.formulas["dbl-2015-rcb"]
    mult = LTRMultiplier(add, dbl)
    privA = mod(int(secg_data["keyA"]["priv"], 16), secp160r1.order)
    pubA_affine = Point(
        affine_model,
        x=mod(int(secg_data["keyA"]["pub"]["x"], 16), secp160r1.curve.prime),
        y=mod(int(secg_data["keyA"]["pub"]["y"], 16), secp160r1.curve.prime),
    )
    pubA = pubA_affine.to_model(secp160r1.curve.coordinate_model, secp160r1.curve)
    privB = mod(int(secg_data["keyB"]["priv"], 16), secp160r1.order)
    pubB_affine = Point(
        affine_model,
        x=mod(int(secg_data["keyB"]["pub"]["x"], 16), secp160r1.curve.prime),
        y=mod(int(secg_data["keyB"]["pub"]["y"], 16), secp160r1.curve.prime),
    )
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


@pytest.mark.parametrize(
    "mult_args",
    [
        (LadderMultiplier, "ladd-1987-m", "dbl-1987-m", "scale"),
        (DifferentialLadderMultiplier, "dadd-1987-m", "dbl-1987-m", "scale"),
    ],
    ids=["ladd", "diff"]
)
@pytest.mark.parametrize("complete", [True, False], ids=["complete", ""])
@pytest.mark.parametrize("short_circuit", [True, False], ids=["shorted", ""])
@pytest.mark.parametrize("full", [True, False], ids=["full", ""])
@pytest.mark.parametrize(
    "scalar_hex,coord_hex,result_hex",
    [
        (
            "A546E36BF0527C9D3B16154B82465EDD62144C0AC1FC5A18506A2244BA449AC4",
            "E6DB6867583030DB3594C1A424B15F7C726624EC26B3353B10A903A6D0AB1C4C",
            "C3DA55379DE9C6908E94EA4DF28D084F32ECCF03491C71F754B4075577A28552",
        ),
        (
            "4b66e9d4d1b4673c5ad22691957d6af5c11b6421e0ea01d42ca4169e7918ba0d",
            "e5210f12786811d3f4b7959d0538ae2c31dbe7106fc03c3efc4cd549c715a493",
            "95cbde9476e8907d7aade45cb4b873f88b595a68799fa152e6f8f7647aac7957",
        ),
        (
            "77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a",
            "de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f",
            "4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742",
        ),
        (
            "5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb",
            "8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a",
            "4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742",
        ),
    ],
    ids=["RFC7748tv1", "RFC7748tv2", "RFC7748dh1", "RFC7748dh2"],
)
def test_x25519(
    curve25519, mult_args, complete, short_circuit, full, scalar_hex, coord_hex, result_hex
):
    mult_class = mult_args[0]
    mult_formulas = list(
        map(
            lambda name: curve25519.curve.coordinate_model.formulas[name], mult_args[1:]
        )
    )
    try:
        multiplier = mult_class(
            *mult_formulas, complete=complete, short_circuit=short_circuit, full=full
        )
    except ValueError:
        return

    scalar = int.from_bytes(bytes.fromhex(scalar_hex), "little")
    coord = int.from_bytes(bytes.fromhex(coord_hex), "little")
    result = bytes.fromhex(result_hex)
    p = curve25519.curve.prime
    coord &= (1 << 255) - 1
    point = Point(curve25519.curve.coordinate_model, X=mod(coord, p), Z=mod(1, p))
    xdh = X25519(multiplier, point, scalar)
    res = xdh.perform()
    assert res == result


@pytest.mark.parametrize(
    "mult_args",
    [
        (LadderMultiplier, "ladd-1987-m", "dbl-1987-m", "scale"),
        (DifferentialLadderMultiplier, "dadd-1987-m", "dbl-1987-m", "scale"),
    ],
    ids=["ladd", "diff"]
)
@pytest.mark.parametrize("complete", [True, False], ids=["complete", ""])
@pytest.mark.parametrize("short_circuit", [True, False], ids=["shorted", ""])
@pytest.mark.parametrize("full", [True, False], ids=["full", ""])
@pytest.mark.parametrize(
    "scalar_hex,coord_hex,result_hex",
    [
        (
            "3d262fddf9ec8e88495266fea19a34d28882acef045104d0d1aae121700a779c984c24f8cdd78fbff44943eba368f54b29259a4f1c600ad3",
            "06fce640fa3487bfda5f6cf2d5263f8aad88334cbd07437f020f08f9814dc031ddbdc38c19c6da2583fa5429db94ada18aa7a7fb4ef8a086",
            "ce3e4ff95a60dc6697da1db1d85e6afbdf79b50a2412d7546d5f239fe14fbaadeb445fc66a01b0779d98223961111e21766282f73dd96b6f",
        ),
        (
            "203d494428b8399352665ddca42f9de8fef600908e0d461cb021f8c538345dd77c3e4806e25f46d3315c44e0a5b4371282dd2c8d5be3095f",
            "0fbcc2f993cd56d3305b0b7d9e55d4c1a8fb5dbb52f8e9a1e9b6201b165d015894e56c4d3570bee52fe205e28a78b91cdfbde71ce8d157db",
            "884a02576239ff7a2f2f63b2db6a9ff37047ac13568e1e30fe63c4a7ad1b3ee3a5700df34321d62077e63633c575c1c954514e99da7c179d",
        ),
        (
            "9a8f4925d1519f5775cf46b04b5800d4ee9ee8bae8bc5565d498c28dd9c9baf574a9419744897391006382a6f127ab1d9ac2d8c0a598726b",
            "3eb7a829b0cd20f5bcfc0b599b6feccf6da4627107bdb0d4f345b43027d8b972fc3e34fb4232a13ca706dcb57aec3dae07bdc1c67bf33609",
            "07fff4181ac6cc95ec1c16a94a0f74d12da232ce40a77552281d282bb60c0b56fd2464c335543936521c24403085d59a449a5037514a879d",
        ),
        (
            "1c306a7ac2a0e2e0990b294470cba339e6453772b075811d8fad0d1d6927c120bb5ee8972b0d3e21374c9c921b09d1b0366f10b65173992d",
            "9b08f7cc31b7e3e67d22d5aea121074a273bd2b83de09c63faa73d2c22c5d9bbc836647241d953d40c5b12da88120d53177f80e532c41fa0",
            "07fff4181ac6cc95ec1c16a94a0f74d12da232ce40a77552281d282bb60c0b56fd2464c335543936521c24403085d59a449a5037514a879d",
        ),
    ],
    ids=["RFC7748tv1", "RFC7748tv2", "RFC7748dh1", "RFC7748dh2"],
)
def test_x448(
    curve448, mult_args, complete, short_circuit, full, scalar_hex, coord_hex, result_hex
):
    mult_class = mult_args[0]
    mult_formulas = list(
        map(lambda name: curve448.curve.coordinate_model.formulas[name], mult_args[1:])
    )
    try:
        multiplier = mult_class(
            *mult_formulas, complete=complete, short_circuit=short_circuit, full=full
        )
    except ValueError:
        return

    scalar = int.from_bytes(bytes.fromhex(scalar_hex), "little")
    coord = int.from_bytes(bytes.fromhex(coord_hex), "little")
    result = bytes.fromhex(result_hex)
    p = curve448.curve.prime

    point = Point(curve448.curve.coordinate_model, X=mod(coord, p), Z=mod(1, p))
    xdh = X448(multiplier, point, scalar)
    res = xdh.perform()
    assert res == result
