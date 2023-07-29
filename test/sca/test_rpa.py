import io
from contextlib import redirect_stdout
from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.context import local
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    LadderMultiplier,
    SimpleLadderMultiplier,
    DifferentialLadderMultiplier
)
from pyecsca.ec.params import get_params, DomainParameters
from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import MultipleContext, rpa_point_0y, rpa_point_x0, rpa_distinguish


class MultipleContextTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.add = self.coords.formulas["add-1998-cmo"]
        self.dbl = self.coords.formulas["dbl-1998-cmo"]
        self.neg = self.coords.formulas["neg"]
        self.scale = self.coords.formulas["z"]

    @parameterized.expand(
        [
            ("5", 5),
            ("10", 10),
            ("2355498743", 2355498743),
            (
                    "325385790209017329644351321912443757746",
                    325385790209017329644351321912443757746,
            ),
            ("13613624287328732", 13613624287328732),
        ]
    )
    def test_basic(self, name, scalar):
        mult = LTRMultiplier(
            self.add,
            self.dbl,
            self.scale,
            always=False,
            complete=False,
            short_circuit=True,
        )
        with local(MultipleContext()) as ctx:
            mult.init(self.secp128r1, self.base)
            mult.multiply(scalar)
        muls = list(ctx.points.values())
        self.assertEqual(muls[-1], scalar)

    def test_precomp(self):
        bnaf = BinaryNAFMultiplier(self.add, self.dbl, self.neg, self.scale)
        with local(MultipleContext()) as ctx:
            bnaf.init(self.secp128r1, self.base)
        muls = list(ctx.points.values())
        self.assertListEqual(muls, [1, -1])

        wnaf = WindowNAFMultiplier(self.add, self.dbl, self.neg, 3, self.scale)
        with local(MultipleContext()) as ctx:
            wnaf.init(self.secp128r1, self.base)
        muls = list(ctx.points.values())
        self.assertListEqual(muls, [1, 2, 3, 5])

    def test_window(self):
        mult = WindowNAFMultiplier(
            self.add, self.dbl, self.neg, 3, precompute_negation=True
        )
        with local(MultipleContext()):
            mult.init(self.secp128r1, self.base)
            mult.multiply(5)

    def test_ladder(self):
        curve25519 = get_params("other", "Curve25519", "xz")
        base = curve25519.generator
        coords = curve25519.curve.coordinate_model
        ladd = coords.formulas["ladd-1987-m"]
        dadd = coords.formulas["dadd-1987-m"]
        dbl = coords.formulas["dbl-1987-m"]
        scale = coords.formulas["scale"]
        ladd_mult = LadderMultiplier(ladd, dbl, scale)
        with local(MultipleContext()) as ctx:
            ladd_mult.init(curve25519, base)
            ladd_mult.multiply(1339278426732672313)
        muls = list(ctx.points.values())
        self.assertEqual(muls[-2], 1339278426732672313)
        dadd_mult = DifferentialLadderMultiplier(dadd, dbl, scale)
        with local(MultipleContext()) as ctx:
            dadd_mult.init(curve25519, base)
            dadd_mult.multiply(1339278426732672313)
        muls = list(ctx.points.values())
        self.assertEqual(muls[-2], 1339278426732672313)


class RPATests(TestCase):

    def setUp(self):
        self.model = ShortWeierstrassModel()
        self.coords = self.model.coordinates["projective"]
        self.add = self.coords.formulas["add-2007-bl"]
        self.dbl = self.coords.formulas["dbl-2007-bl"]
        self.neg = self.coords.formulas["neg"]

    def test_x0_point(self):
        p = 0x85d265945a4f5681
        a = Mod(0x7fc57b4110698bc0, p)
        b = Mod(0x37113ea591b04527, p)
        gx = Mod(0x80d2d78fddb97597, p)
        gy = Mod(0x5586d818b7910930, p)
        # (0x4880bcf620852a54, 0) RPA point

        infty = Point(self.coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p))
        g = Point(self.coords, X=gx, Y=gy, Z=Mod(1, p))
        curve = EllipticCurve(self.model, self.coords, p, infty, dict(a=a, b=b))
        params_full = DomainParameters(curve, g, 0x85d265932d90785c, 1)

        self.assertIsNotNone(rpa_point_x0(params_full))

    def test_0y_point(self):
        p = 0x85d265945a4f5681
        a = Mod(0x7fc57b4110698bc0, p)
        b = Mod(0x37113ea591b04527, p)
        gx = Mod(0x80d2d78fddb97597, p)
        gy = Mod(0x5586d818b7910930, p)
        # (0, 0x6bed3155c9ada064) RPA point

        infty = Point(self.coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p))
        g = Point(self.coords, X=gx, Y=gy, Z=Mod(1, p))
        curve = EllipticCurve(self.model, self.coords, p, infty, dict(a=a, b=b))
        params_full = DomainParameters(curve, g, 0x85d265932d90785c, 1)

        self.assertIsNotNone(rpa_point_0y(params_full))

    def test_distinguish(self):
        secp128r1 = get_params("secg", "secp128r1", "projective")
        multipliers = [LTRMultiplier(self.add, self.dbl, None, False, True, True),
                       LTRMultiplier(self.add, self.dbl, None, True, True, True),
                       RTLMultiplier(self.add, self.dbl, None, False, True),
                       RTLMultiplier(self.add, self.dbl, None, True, True),
                       SimpleLadderMultiplier(self.add, self.dbl, None, True, True),
                       BinaryNAFMultiplier(self.add, self.dbl, self.neg, None, True),
                       WindowNAFMultiplier(self.add, self.dbl, self.neg, 3, None, True),
                       WindowNAFMultiplier(self.add, self.dbl, self.neg, 4, None, True)]
        for real_mult in multipliers:
            def simulated_oracle(scalar, affine_point):
                point = affine_point.to_model(secp128r1.curve.coordinate_model, secp128r1.curve)
                with local(MultipleContext()) as ctx:
                    real_mult.init(secp128r1, point)
                    real_mult.multiply(scalar)
                return any(map(lambda P: P.X == 0 or P.Y == 0, ctx.points.keys()))

            with redirect_stdout(io.StringIO()):
                result = rpa_distinguish(secp128r1, multipliers, simulated_oracle)
            self.assertEqual(1, len(result))
            self.assertEqual(real_mult, result[0])
