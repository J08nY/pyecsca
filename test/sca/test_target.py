from copy import copy
from os.path import realpath, dirname, join
from typing import Optional
from unittest import TestCase, SkipTest

from smartcard.pcsc.PCSCExceptions import BaseSCardException

from pyecsca.ec.key_agreement import ECDH_SHA1
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import DomainParameters, get_params
from pyecsca.ec.point import Point
from pyecsca.ec.signature import SignatureResult, ECDSA_SHA1
from pyecsca.sca.target import BinaryTarget, SimpleSerialTarget, SimpleSerialMessage, has_pyscard
from pyecsca.sca.target.ectester import (KeyAgreementEnum, SignatureEnum, KeypairEnum, KeyBuildEnum,
                                         KeyClassEnum, CurveEnum, ParameterEnum, RunModeEnum,
                                         KeyEnum, TransformationEnum)

if has_pyscard:
    from pyecsca.sca.target.ectester import ECTesterTarget
else:
    ECTesterTarget = None


class TestTarget(SimpleSerialTarget, BinaryTarget):
    pass


class BinaryTargetTests(TestCase):

    def test_basic_target(self):
        target_path = join(dirname(realpath(__file__)), "..", "data", "target.py")
        target = TestTarget(["python", target_path])
        target.connect()
        resp = target.send_cmd(SimpleSerialMessage("d", ""), 500)
        self.assertIn("r", resp)
        self.assertIn("z", resp)
        self.assertEqual(resp["r"].data, "01020304")
        target.disconnect()

    def test_debug(self):
        target_path = join(dirname(realpath(__file__)), "..", "data", "target.py")
        target = TestTarget(["python", target_path], debug_output=True)
        target.connect()
        target.send_cmd(SimpleSerialMessage("d", ""), 500)
        target.disconnect()

    def test_no_connection(self):
        target_path = join(dirname(realpath(__file__)), "..", "data", "target.py")
        target = TestTarget(target_path)
        with self.assertRaises(ValueError):
            target.write(bytes([1, 2, 3, 4]))
        with self.assertRaises(ValueError):
            target.read(5)
        target.disconnect()


class ECTesterTargetTests(TestCase):
    reader: Optional[str] = None
    target: Optional[ECTesterTarget] = None
    secp256r1: DomainParameters
    secp256r1_projective: DomainParameters

    @classmethod
    def setUpClass(cls):
        if not has_pyscard:
            return
        from smartcard.System import readers
        try:
            rs = readers()
        except BaseSCardException:
            return
        if not rs:
            return
        cls.reader = rs[0]
        cls.secp256r1 = get_params("secg", "secp256r1", "affine")
        cls.secp256r1_projective = get_params("secg", "secp256r1", "projective")

    def setUp(self):
        if not ECTesterTargetTests.reader:
            raise SkipTest("No smartcard readers.")
        self.target = ECTesterTarget(ECTesterTargetTests.reader)
        self.target.connect()
        if not self.target.select_applet():
            self.target.disconnect()
            raise SkipTest("No applet in reader: {}".format(ECTesterTargetTests.reader))

    def tearDown(self):
        self.target.cleanup()
        self.target.disconnect()

    def test_allocate(self):
        ka_resp = self.target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
        self.assertTrue(ka_resp.success)
        sig_resp = self.target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
        self.assertTrue(sig_resp.success)
        key_resp = self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                                        KeyClassEnum.ALG_EC_FP)
        self.assertTrue(key_resp.success)

    def test_set(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        set_resp = self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1,
                                   ParameterEnum.DOMAIN_FP)
        self.assertTrue(set_resp.success)

    def test_set_explicit(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        values = ECTesterTarget.encode_parameters(ParameterEnum.DOMAIN_FP, self.secp256r1)
        set_resp = self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.external,
                                   ParameterEnum.DOMAIN_FP, values)
        self.assertTrue(set_resp.success)

    def test_generate(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        generate_resp = self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        self.assertTrue(generate_resp.success)

    def test_clear(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        clear_resp = self.target.clear(KeypairEnum.KEYPAIR_LOCAL)
        self.assertTrue(clear_resp.success)

    def test_cleanup(self):
        cleanup_resp = self.target.cleanup()
        self.assertTrue(cleanup_resp.success)

    def test_info(self):
        info_resp = self.target.info()
        self.assertTrue(info_resp.success)

    def test_dry_run(self):
        dry_run_resp = self.target.run_mode(RunModeEnum.MODE_DRY_RUN)
        self.assertTrue(dry_run_resp.success)
        allocate_resp = self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR,
                                             256,
                                             KeyClassEnum.ALG_EC_FP)
        self.assertTrue(allocate_resp.success)
        dry_run_resp = self.target.run_mode(RunModeEnum.MODE_NORMAL)
        self.assertTrue(dry_run_resp.success)

    def test_export(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        export_public_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC,
                                                ParameterEnum.W)
        self.assertTrue(export_public_resp.success)
        pubkey_bytes = export_public_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W)
        pubkey = self.secp256r1.curve.decode_point(pubkey_bytes)
        export_privkey_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE,
                                                 ParameterEnum.S)
        self.assertTrue(export_privkey_resp.success)
        privkey = int.from_bytes(
                export_privkey_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S), "big")
        self.assertEqual(pubkey,
                         self.secp256r1.curve.affine_multiply(self.secp256r1.generator, privkey))

    def test_export_curve(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        export_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC,
                                         ParameterEnum.DOMAIN_FP)
        self.assertTrue(export_resp.success)

    def test_transform(self):
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        export_privkey_resp1 = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE,
                                                  ParameterEnum.S)
        privkey = int.from_bytes(
                export_privkey_resp1.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S), "big")
        transform_resp = self.target.transform(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE,
                                               ParameterEnum.S, TransformationEnum.INCREMENT)
        self.assertTrue(transform_resp.success)
        export_privkey_resp2 = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE,
                                                  ParameterEnum.S)
        privkey_new = int.from_bytes(
                export_privkey_resp2.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S), "big")
        self.assertEqual(privkey + 1, privkey_new)

    def test_ecdh(self):
        self.target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
        self.target.allocate(KeypairEnum.KEYPAIR_BOTH, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_BOTH, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_BOTH)
        ecdh_resp = self.target.ecdh(KeypairEnum.KEYPAIR_LOCAL, KeypairEnum.KEYPAIR_REMOTE, True,
                                     TransformationEnum.NONE, KeyAgreementEnum.ALG_EC_SVDP_DH)
        self.assertTrue(ecdh_resp.success)
        export_public_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC,
                                                ParameterEnum.W)
        pubkey_bytes = export_public_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W)
        pubkey = self.secp256r1.curve.decode_point(pubkey_bytes)
        export_privkey_resp = self.target.export(KeypairEnum.KEYPAIR_REMOTE, KeyEnum.PRIVATE,
                                                 ParameterEnum.S)
        privkey = Mod(int.from_bytes(
                export_privkey_resp.get_param(KeypairEnum.KEYPAIR_REMOTE, ParameterEnum.S), "big"),
                self.secp256r1.curve.prime)
        pubkey_projective = pubkey.to_model(self.secp256r1_projective.curve.coordinate_model, self.secp256r1.curve)

        mult = LTRMultiplier(
                self.secp256r1_projective.curve.coordinate_model.formulas["add-2016-rcb"],
                self.secp256r1_projective.curve.coordinate_model.formulas["dbl-2016-rcb"])
        ecdh = ECDH_SHA1(mult, self.secp256r1_projective, pubkey_projective, privkey)
        expected = ecdh.perform()
        self.assertEqual(ecdh_resp.secret, expected)

    def test_ecdh_raw(self):
        self.target.allocate_ka(KeyAgreementEnum.ALG_EC_SVDP_DH)
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        mult = LTRMultiplier(
                self.secp256r1_projective.curve.coordinate_model.formulas["add-2016-rcb"],
                self.secp256r1_projective.curve.coordinate_model.formulas["dbl-2016-rcb"])
        keygen = KeyGeneration(copy(mult), self.secp256r1_projective)
        priv, pubkey_projective = keygen.generate()

        ecdh_resp = self.target.ecdh_direct(KeypairEnum.KEYPAIR_LOCAL, True,
                                            TransformationEnum.NONE,
                                            KeyAgreementEnum.ALG_EC_SVDP_DH,
                                            bytes(pubkey_projective.to_affine()))
        self.assertTrue(ecdh_resp.success)
        export_privkey_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PRIVATE,
                                                 ParameterEnum.S)
        privkey = Mod(int.from_bytes(
                export_privkey_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.S), "big"),
                self.secp256r1.curve.prime)

        ecdh = ECDH_SHA1(copy(mult), self.secp256r1_projective, pubkey_projective, privkey)
        expected = ecdh.perform()
        self.assertEqual(ecdh_resp.secret, expected)

    def test_ecdsa(self):
        self.target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        data = "Some text over here.".encode()
        ecdsa_resp = self.target.ecdsa(KeypairEnum.KEYPAIR_LOCAL, True, SignatureEnum.ALG_ECDSA_SHA,
                                       data)
        self.assertTrue(ecdsa_resp.success)
        export_public_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC,
                                                ParameterEnum.W)
        pubkey_bytes = export_public_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W)
        pubkey = self.secp256r1.curve.decode_point(pubkey_bytes)
        pubkey_projective = pubkey.to_model(self.secp256r1_projective.curve.coordinate_model, self.secp256r1.curve)

        sig = SignatureResult.from_DER(ecdsa_resp.signature)
        mult = LTRMultiplier(
                self.secp256r1_projective.curve.coordinate_model.formulas["add-2016-rcb"],
                self.secp256r1_projective.curve.coordinate_model.formulas["dbl-2016-rcb"])
        ecdsa = ECDSA_SHA1(copy(mult), self.secp256r1_projective,
                           self.secp256r1_projective.curve.coordinate_model.formulas[
                               "add-2016-rcb"],
                           pubkey_projective)
        self.assertTrue(ecdsa.verify_data(sig, data))

    def test_ecdsa_sign(self):
        self.target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        self.target.generate(KeypairEnum.KEYPAIR_LOCAL)
        data = "Some text over here.".encode()
        ecdsa_resp = self.target.ecdsa_sign(KeypairEnum.KEYPAIR_LOCAL, True,
                                            SignatureEnum.ALG_ECDSA_SHA, data)
        self.assertTrue(ecdsa_resp.success)
        export_public_resp = self.target.export(KeypairEnum.KEYPAIR_LOCAL, KeyEnum.PUBLIC,
                                                ParameterEnum.W)
        pubkey_bytes = export_public_resp.get_param(KeypairEnum.KEYPAIR_LOCAL, ParameterEnum.W)
        pubkey = self.secp256r1.curve.decode_point(pubkey_bytes)
        pubkey_projective = pubkey.to_model(self.secp256r1_projective.curve.coordinate_model, self.secp256r1.curve)

        sig = SignatureResult.from_DER(ecdsa_resp.signature)
        mult = LTRMultiplier(
                self.secp256r1_projective.curve.coordinate_model.formulas["add-2016-rcb"],
                self.secp256r1_projective.curve.coordinate_model.formulas["dbl-2016-rcb"])
        ecdsa = ECDSA_SHA1(copy(mult), self.secp256r1_projective,
                           self.secp256r1_projective.curve.coordinate_model.formulas[
                               "add-2016-rcb"],
                           pubkey_projective)
        self.assertTrue(ecdsa.verify_data(sig, data))

    def test_ecdsa_verify(self):
        self.target.allocate_sig(SignatureEnum.ALG_ECDSA_SHA)
        self.target.allocate(KeypairEnum.KEYPAIR_LOCAL, KeyBuildEnum.BUILD_KEYPAIR, 256,
                             KeyClassEnum.ALG_EC_FP)
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.secp256r1, ParameterEnum.DOMAIN_FP)
        mult = LTRMultiplier(
                self.secp256r1_projective.curve.coordinate_model.formulas["add-2016-rcb"],
                self.secp256r1_projective.curve.coordinate_model.formulas["dbl-2016-rcb"])
        keygen = KeyGeneration(copy(mult), self.secp256r1_projective)
        priv, pubkey_projective = keygen.generate()
        self.target.set(KeypairEnum.KEYPAIR_LOCAL, CurveEnum.external, ParameterEnum.W,
                        ECTesterTarget.encode_parameters(ParameterEnum.W,
                                                         pubkey_projective.to_affine()))
        ecdsa = ECDSA_SHA1(copy(mult), self.secp256r1_projective,
                           self.secp256r1_projective.curve.coordinate_model.formulas[
                               "add-2016-rcb"],
                           pubkey_projective,
                           priv)
        data = "Some text over here.".encode()
        sig = ecdsa.sign_data(data)

        ecdsa_resp = self.target.ecdsa_verify(KeypairEnum.KEYPAIR_LOCAL,
                                              SignatureEnum.ALG_ECDSA_SHA, sig.to_DER(), data)
        self.assertTrue(ecdsa_resp.success)
