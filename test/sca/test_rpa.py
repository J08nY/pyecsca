from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.context import local
from pyecsca.ec.mult import (
    LTRMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    LadderMultiplier,
    DifferentialLadderMultiplier,
)
from pyecsca.ec.params import get_params
from pyecsca.sca.re.rpa import MultipleContext


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
        mult = WindowNAFMultiplier(self.add, self.dbl, self.neg, 3, precompute_negation=True)
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
