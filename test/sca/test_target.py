import hashlib
import io
from contextlib import redirect_stdout
from copy import copy

import pytest
from importlib_resources import files, as_file

import test.data.sca
from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import get_params
from pyecsca.ec.signature import SignatureResult, ECDSA_SHA1
from pyecsca.sca.target import (
    BinaryTarget,
    SimpleSerialTarget,
    SimpleSerialMessage,
    has_pyscard,
    LeakageTarget,
)
from pyecsca.sca.attack import HammingWeight
from pyecsca.sca.target.ectester import (
    KeyAgreementEnum,
    SignatureEnum,
    KeypairEnum,
    KeyBuildEnum,
    KeyClassEnum,
    CurveEnum,
    ParameterEnum,
    RunModeEnum,
    KeyEnum,
    TransformationEnum,
)

if has_pyscard:
    from pyecsca.sca.target.ectester import ECTesterTargetPCSC as ECTesterTarget
else:
    from pyecsca.sca.target.ectester import ECTesterTarget  # type: ignore


class TestTarget(SimpleSerialTarget, BinaryTarget):
    __test__ = False


def test_basic_target():
    with as_file(files(test.data.sca).joinpath("target.py")) as target_path:
        target = TestTarget(["python", target_path])
        target.connect()
        resp = target.send_cmd(SimpleSerialMessage("d", ""), 500)
        assert "r" in resp
        assert "z" in resp
        assert resp["r"].data == "01020304"
        target.disconnect()


def test_debug():
    with as_file(files(test.data.sca).joinpath("target.py")) as target_path:
        target = TestTarget(["python", target_path], debug_output=True)
        with redirect_stdout(io.StringIO()) as out:
            target.connect()
            target.send_cmd(SimpleSerialMessage("d", ""), 500)
            target.disconnect()
        assert out.read() is not None


def test_no_connection():
    with as_file(files(test.data.sca).joinpath("target.py")) as target_path:
        target = TestTarget(str(target_path))
        with pytest.raises(ValueError):
            target.write(bytes([1, 2, 3, 4]))
        with pytest.raises(ValueError):
            target.read(5)
        target.disconnect()


@pytest.fixture()
def secp256r1_affine():
    return get_params("secg", "secp256r1", "affine")


@pytest.fixture()
def secp256r1_projective():
    return get_params("secg", "secp256r1", "projective")


@pytest.fixture()
def target():
    if not has_pyscard:
        pytest.skip("No pyscard.")
    from smartcard.System import readers
    from smartcard.pcsc.PCSCExceptions import BaseSCardException
    rs = None
    try:
        rs = readers()
    except BaseSCardException as e:
        pytest.skip(f"No reader found: {e}")
    if not rs:
        pytest.skip("No reader found")
    reader = rs[0]  # type: ignore
    target: ECTesterTarget = ECTesterTarget(reader)  # This will not instantiate an abstract class, skipcq: PYL-E0110
    target.connect()
    if not target.select_applet():
        target.disconnect()
        pytest.skip(f"No applet in reader: {reader}")
    yield target
    target.cleanup()
    target.disconnect()


def test_allocate(target):
    ka_resp = target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
    assert ka_resp.success
    sig_resp = target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
    assert sig_resp.success
    key_resp = target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    assert key_resp.success


def test_set(target):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    set_resp = target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    assert set_resp.success


def test_set_explicit(target, secp256r1_affine):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    values = ECTesterTarget.encode_parameters(
        ParameterEnum.DOMAIN_FP, secp256r1_affine
    )
    set_resp = target.set(
        KeypairEnum.KEYPAIR_LOCAL,
        CurveEnum.external,
        ParameterEnum.DOMAIN_FP,
        values,
    )
    assert set_resp.success


def test_generate(target):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    generate_resp = target.generate(KeypairEnum.KEYPAIR_LOCAL)
    assert generate_resp.success


def test_clear(target):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    clear_resp = target.clear(KeypairEnum.KEYPAIR_LOCAL)
    assert clear_resp.success


def test_cleanup(target):
    cleanup_resp = target.cleanup()
    assert cleanup_resp.success


def test_info(target):
    info_resp = target.info()
    assert info_resp.success


def test_dry_run(target):
    dry_run_resp = target.run_mode(RunModeEnum.MODE_DRY_RUN)
    assert dry_run_resp.success
    allocate_resp = target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    assert allocate_resp.success
    dry_run_resp = target.run_mode(RunModeEnum.MODE_NORMAL)
    assert dry_run_resp.success


def test_export(target, secp256r1_affine):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_LOCAL)
    export_public_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC, ParameterEnum.W
    )
    assert export_public_resp.success
    pubkey_bytes = export_public_resp.get_param(
        KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W
    )
    pubkey = secp256r1_affine.curve.decode_point(pubkey_bytes)
    export_privkey_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE, ParameterEnum.S
    )
    assert export_privkey_resp.success
    privkey = int.from_bytes(
        export_privkey_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S),
        "big",
    )
    assert pubkey == \
           secp256r1_affine.curve.affine_multiply(secp256r1_affine.generator, privkey)


def test_export_curve(target):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    export_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC, ParameterEnum.DOMAIN_FP
    )
    assert export_resp.success


def test_transform(target):
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_LOCAL)
    export_privkey_resp1 = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE, ParameterEnum.S
    )
    privkey = int.from_bytes(
        export_privkey_resp1.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S),
        "big",
    )
    transform_resp = target.transform(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyEnum.PRIVATE,
        ParameterEnum.S,
        TransformationEnum.INCREMENT,
    )
    assert transform_resp.success
    export_privkey_resp2 = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE, ParameterEnum.S
    )
    privkey_new = int.from_bytes(
        export_privkey_resp2.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S),
        "big",
    )
    assert privkey + 1 == privkey_new


def test_ecdh(target, secp256r1_affine, secp256r1_projective):
    target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
    target.allocate(
        KeypairEnum.KEYPAIR_BOTH,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_BOTH, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_BOTH)
    ecdh_resp = target.ecdh(
        KeypairEnum.KEYPAIR_LOCAL,
        KeypairEnum.KEYPAIR_REMOTE,
        True,
        TransformationEnum.NONE,
        KeyAgreementEnum.ALG_EC_SVDP_DH,
    )
    assert ecdh_resp.success
    export_public_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC, ParameterEnum.W
    )
    pubkey_bytes = export_public_resp.get_param(
        KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W
    )
    pubkey = secp256r1_affine.curve.decode_point(pubkey_bytes)
    export_privkey_resp = target.export(
        KeypairEnum.KEYPAIR_REMOTE, KeyEnum.PRIVATE, ParameterEnum.S
    )
    privkey = Mod(
        int.from_bytes(
            export_privkey_resp.get_param(
                KeypairEnum.KEYPAIR_REMOTE, ParameterEnum.S
            ),
            "big",
        ),
        secp256r1_affine.curve.prime,
    )
    pubkey_projective = pubkey.to_model(
        secp256r1_projective.curve.coordinate_model, secp256r1_affine.curve
    )

    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    ecdh = ECDH_SHA1(mult, secp256r1_projective, pubkey_projective, privkey)
    expected = ecdh.perform()
    assert ecdh_resp.secret == expected


def test_ecdh_raw(target, secp256r1_projective):
    target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_LOCAL)
    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    keygen = KeyGeneration(copy(mult), secp256r1_projective)
    _, pubkey_projective = keygen.generate()

    ecdh_resp = target.ecdh_direct(
        KeypairEnum.KEYPAIR_LOCAL,
        True,
        TransformationEnum.NONE,
        KeyAgreementEnum.ALG_EC_SVDP_DH,
        bytes(pubkey_projective.to_affine()),
    )
    assert ecdh_resp.success
    export_privkey_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE, ParameterEnum.S
    )
    privkey = Mod(
        int.from_bytes(
            export_privkey_resp.get_param(
                KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S
            ),
            "big",
        ),
        secp256r1_projective.curve.prime,
    )

    ecdh = ECDH_SHA1(
        copy(mult), secp256r1_projective, pubkey_projective, privkey
    )
    expected = ecdh.perform()
    assert ecdh_resp.secret == expected


def test_ecdsa(target, secp256r1_affine, secp256r1_projective):
    target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_LOCAL)
    data = "Some text over here.".encode()
    ecdsa_resp = target.ecdsa(
        KeypairEnum.KEYPAIR_LOCAL, True, SignatureEnum.ALG_ECDSA_SHA, data
    )
    assert ecdsa_resp.success
    export_public_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC, ParameterEnum.W
    )
    pubkey_bytes = export_public_resp.get_param(
        KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W
    )
    pubkey = secp256r1_affine.curve.decode_point(pubkey_bytes)
    pubkey_projective = pubkey.to_model(
        secp256r1_projective.curve.coordinate_model, secp256r1_affine.curve
    )

    sig = SignatureResult.from_DER(ecdsa_resp.signature)
    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    ecdsa = ECDSA_SHA1(
        copy(mult),
        secp256r1_projective,
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        pubkey_projective,
    )
    assert ecdsa.verify_data(sig, data)


def test_ecdsa_sign(target, secp256r1_affine, secp256r1_projective):
    target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    target.generate(KeypairEnum.KEYPAIR_LOCAL)
    data = "Some text over here.".encode()
    ecdsa_resp = target.ecdsa_sign(
        KeypairEnum.KEYPAIR_LOCAL, True, SignatureEnum.ALG_ECDSA_SHA, data
    )
    assert ecdsa_resp.success
    export_public_resp = target.export(
        KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC, ParameterEnum.W
    )
    pubkey_bytes = export_public_resp.get_param(
        KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W
    )
    pubkey = secp256r1_affine.curve.decode_point(pubkey_bytes)
    pubkey_projective = pubkey.to_model(
        secp256r1_projective.curve.coordinate_model, secp256r1_affine.curve
    )

    sig = SignatureResult.from_DER(ecdsa_resp.signature)
    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    ecdsa = ECDSA_SHA1(
        copy(mult),
        secp256r1_projective,
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        pubkey_projective,
    )
    assert ecdsa.verify_data(sig, data)


def test_ecdsa_verify(target, secp256r1_projective):
    target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
    target.allocate(
        KeypairEnum.KEYPAIR_LOCAL,
        KeyBuildEnum.BUILD_KEYPAIR,
        256,
        KeyClassEnum.ALG_EC_FP,
    )
    target.set(
        KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP
    )
    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    keygen = KeyGeneration(copy(mult), secp256r1_projective)
    priv, pubkey_projective = keygen.generate()
    target.set(
        KeypairEnum.KEYPAIR_LOCAL,
        CurveEnum.external,
        ParameterEnum.W,
        ECTesterTarget.encode_parameters(
            ParameterEnum.W, pubkey_projective.to_affine()
        ),
    )
    ecdsa = ECDSA_SHA1(
        copy(mult),
        secp256r1_projective,
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        pubkey_projective,
        priv,
    )
    data = "Some text over here.".encode()
    sig = ecdsa.sign_data(data)

    ecdsa_resp = target.ecdsa_verify(
        KeypairEnum.KEYPAIR_LOCAL, SignatureEnum.ALG_ECDSA_SHA, sig.to_DER(), data
    )
    assert ecdsa_resp.success


def test_leakage_target(secp256r1_projective):
    mult = LTRMultiplier(
        secp256r1_projective.curve.coordinate_model.formulas["add-2015-rcb"],
        secp256r1_projective.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    lm = HammingWeight()
    target = LeakageTarget(secp256r1_projective.curve.model, secp256r1_projective.curve.coordinate_model, mult, lm)
    target.set_params(secp256r1_projective)
    (priv, pub), trace = target.generate()
    assert trace is not None
    (other_priv, other_pub), trace = target.generate()
    target.set_privkey(priv)
    target.set_pubkey(pub)
    secret, trace = target.ecdh(other_pub)
    target.set_privkey(other_priv)
    target.set_pubkey(other_pub)
    secret2, trace = target.ecdh(pub)
    assert secret == secret2
    res, trace = target.scalar_mult(7, secp256r1_projective.generator)
    assert res is not None

    msg = b"data"
    signature, trace = target.ecdsa_sign(msg, hashlib.sha1)
    assert target.ecdsa_verify(msg, signature, hashlib.sha1)
