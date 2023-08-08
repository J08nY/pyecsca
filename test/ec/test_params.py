from unittest import TestCase

from parameterized import parameterized
from importlib.resources import files, as_file

import test.data.ec
from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.params import get_params, load_params, load_category, get_category, DomainParameters, \
    load_params_ectester, load_params_ecgen
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.curve import EllipticCurve


class DomainParameterTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.curve25519 = get_params("other", "Curve25519", "xz")

    def test_eq(self):
        self.assertEqual(self.secp128r1, self.secp128r1)
        self.assertNotEqual(self.secp128r1, self.curve25519)
        self.assertNotEqual(self.secp128r1, None)

    def test_str(self):
        self.assertEqual(str(self.secp128r1), "DomainParameters(secg/secp128r1)")

    @parameterized.expand(
        [
            ("secg/secp128r1", "projective"),
            ("secg/secp256r1", "projective"),
            ("secg/secp521r1", "projective"),
            ("other/Curve25519", "xz"),
            ("other/Ed25519", "projective"),
            ("other/Ed448", "projective"),
            ("other/E-222", "projective"),
        ]
    )
    def test_get_params(self, name, coords):
        params = get_params(*name.split("/"), coords)
        try:
            assert params.curve.is_on_curve(params.generator)
        except NotImplementedError:
            pass

    @parameterized.expand(
        [
            ("anssi", "projective"),
            (
                    "brainpool",
                    lambda name: "projective" if name.endswith("r1") else "jacobian",
            ),
        ]
    )
    def test_get_category(self, name, coords):
        get_category(name, coords)

    def test_load_params(self):
        with as_file(files(test.data.ec).joinpath("curve.json")) as path:
            params = load_params(path, "projective")
            try:
                assert params.curve.is_on_curve(params.generator)
            except NotImplementedError:
                pass

    def test_load_params_ectester(self):
        with as_file(files(test.data.ec).joinpath("ectester_secp128r1.csv")) as path:
            params = load_params_ectester(path, "projective")
            assert params.curve.is_on_curve(params.generator)
            self.assertEqual(params, self.secp128r1)

    def test_load_params_ecgen(self):
        with as_file(files(test.data.ec).joinpath("ecgen_secp128r1.json")) as path:
            params = load_params_ecgen(path, "projective")
            assert params.curve.is_on_curve(params.generator)
            self.assertEqual(params, self.secp128r1)

    def test_load_category(self):
        with as_file(files(test.data.ec).joinpath("curves.json")) as path:
            category = load_category(path, "yz")
            self.assertEqual(len(category), 1)

    @parameterized.expand(
        [
            ("no_category/some", "else"),
            ("secg/no_curve", "else"),
            ("secg/secp128r1", "some"),
        ]
    )
    def test_unknown(self, name, coords):
        with self.assertRaises(ValueError):
            get_params(*name.split("/"), coords)

    def test_assumption(self):
        with self.assertRaises(UnsatisfiedAssumptionError):
            get_params("secg", "secp128r1", "projective-1")
        with TemporaryConfig() as cfg:
            cfg.ec.unsatisfied_coordinate_assumption_action = "ignore"
            params = get_params("secg", "secp128r1", "projective-1")
            self.assertIsNotNone(params)
        self.assertIsNotNone(get_params("secg", "secp128r1", "projective-3"))

    def test_infty(self):
        with self.assertRaises(ValueError):
            get_params("other", "Ed25519", "modified", False)
        self.assertIsNotNone(get_params("secg", "secp128r1", "projective", False))

    def test_no_binary(self):
        with self.assertRaises(ValueError):
            get_params("secg", "sect163r1", "something")

    def test_no_extension(self):
        with self.assertRaises(ValueError):
            get_params("other", "Fp254n2BNa", "something")

    def test_affine(self):
        aff = get_params("secg", "secp128r1", "affine")
        self.assertIsInstance(aff.curve.coordinate_model, AffineCoordinateModel)

    def test_custom_params(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        p = 0xd7d1247f
        a = Mod(0xa4a44016, p)
        b = Mod(0x73f76716, p)
        n = 0xd7d2a475
        h = 1
        gx, gy, gz = Mod(0x54eed6d7, p), Mod(0x6f1e55ac, p), Mod(1, p)
        generator = Point(coords, X=gx, Y=gy, Z=gz)
        neutral = InfinityPoint(coords)

        curve = EllipticCurve(model, coords, p, neutral, {"a": a, "b": b})
        params = DomainParameters(curve, generator, n, h)
        self.assertIsNotNone(params)
        res = params.curve.affine_double(generator.to_affine())
        self.assertIsNotNone(res)
