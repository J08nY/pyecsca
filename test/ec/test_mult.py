from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.params import get_params
from pyecsca.ec.mult import (LTRMultiplier, RTLMultiplier, LadderMultiplier, BinaryNAFMultiplier,
                             WindowNAFMultiplier, SimpleLadderMultiplier,
                             DifferentialLadderMultiplier,
                             CoronMultiplier)
from pyecsca.ec.point import InfinityPoint
from .utils import cartesian


class ScalarMultiplierTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model

        self.curve25519 = get_params("other", "Curve25519", "xz")
        self.base25519 = self.curve25519.generator
        self.coords25519 = self.curve25519.curve.coordinate_model

    def get_formulas(self, coords, *names):
        return [coords.formulas[name] for name in names if name is not None]

    def assertPointEquality(self, one, other, scale):
        if scale:
            self.assertEqual(one, other)
        else:
            assert one.equals(other)

    def do_basic_test(self, mult_class, params, base, add, dbl, scale, neg=None, **kwargs):
        mult = mult_class(*self.get_formulas(params.curve.coordinate_model, add, dbl, neg, scale),
                          **kwargs)
        mult.init(params, base)
        res = mult.multiply(314)
        other = mult.multiply(157)
        mult.init(params, other)
        other = mult.multiply(2)
        self.assertPointEquality(res, other, scale)
        mult.init(params, base)
        self.assertEqual(InfinityPoint(params.curve.coordinate_model), mult.multiply(0))
        return res

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_rtl(self, name, add, dbl, scale):
        self.do_basic_test(RTLMultiplier, self.secp128r1, self.base, add, dbl, scale)

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_ltr(self, name, add, dbl, scale):
        a = self.do_basic_test(LTRMultiplier, self.secp128r1, self.base, add, dbl, scale)
        b = self.do_basic_test(LTRMultiplier, self.secp128r1, self.base, add, dbl, scale,
                               always=True)
        c = self.do_basic_test(LTRMultiplier, self.secp128r1, self.base, add, dbl, scale,
                               complete=False)
        d = self.do_basic_test(LTRMultiplier, self.secp128r1, self.base, add, dbl, scale,
                               always=True,
                               complete=False)
        self.assertPointEquality(a, b, scale)
        self.assertPointEquality(b, c, scale)
        self.assertPointEquality(c, d, scale)

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_coron(self, name, add, dbl, scale):
        self.do_basic_test(CoronMultiplier, self.secp128r1, self.base, add, dbl, scale)

    def test_ladder(self):
        a = self.do_basic_test(LadderMultiplier, self.curve25519, self.base25519, "ladd-1987-m",
                               "dbl-1987-m", "scale")
        b = self.do_basic_test(LadderMultiplier, self.curve25519, self.base25519, "ladd-1987-m",
                               "dbl-1987-m", "scale", complete=False)
        self.assertPointEquality(a, b, True)

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_simple_ladder(self, name, add, dbl, scale):
        self.do_basic_test(SimpleLadderMultiplier, self.secp128r1, self.base, add, dbl, scale)

    @parameterized.expand([
        ("15", 15, True),
        ("15", 15, False),
        ("2355498743", 2355498743, True),
        ("2355498743", 2355498743, False),
        ("325385790209017329644351321912443757746", 325385790209017329644351321912443757746, True),
        ("325385790209017329644351321912443757746", 325385790209017329644351321912443757746, False)
    ])
    def test_ladder_differential(self, name, num, complete):
        ladder = LadderMultiplier(self.coords25519.formulas["ladd-1987-m"],
                                  self.coords25519.formulas["dbl-1987-m"],
                                  self.coords25519.formulas["scale"], complete=complete)
        differential = DifferentialLadderMultiplier(self.coords25519.formulas["dadd-1987-m"],
                                                    self.coords25519.formulas["dbl-1987-m"],
                                                    self.coords25519.formulas["scale"],
                                                    complete=complete)
        ladder.init(self.curve25519, self.base25519)
        res_ladder = ladder.multiply(num)
        differential.init(self.curve25519, self.base25519)
        res_differential = differential.multiply(num)
        self.assertEqual(res_ladder, res_differential)
        self.assertEqual(InfinityPoint(self.coords25519), differential.multiply(0))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "neg", "z"),
        ("complete", "add-2016-rcb", "dbl-2016-rcb", "neg", None),
        ("none", "add-1998-cmo", "dbl-1998-cmo", "neg", None)
    ])
    def test_binary_naf(self, name, add, dbl, neg, scale):
        self.do_basic_test(BinaryNAFMultiplier, self.secp128r1, self.base, add, dbl, scale, neg)

    @parameterized.expand([
        ("scaled3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, "z"),
        ("none3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, None),
        ("complete3", "add-2016-rcb", "dbl-2016-rcb", "neg", 3, None),
        ("scaled5", "add-1998-cmo", "dbl-1998-cmo", "neg", 5, "z"),
        ("none5", "add-1998-cmo", "dbl-1998-cmo", "neg", 5, None),
        ("complete5", "add-2016-rcb", "dbl-2016-rcb", "neg", 5, None),
    ])
    def test_window_naf(self, name, add, dbl, neg, width, scale):
        formulas = self.get_formulas(self.coords, add, dbl, neg, scale)
        mult = WindowNAFMultiplier(*formulas[:3], width, *formulas[3:])
        mult.init(self.secp128r1, self.base)
        res = mult.multiply(157 * 789)
        other = mult.multiply(157)
        mult.init(self.secp128r1, other)
        other = mult.multiply(789)
        self.assertPointEquality(res, other, scale)
        mult.init(self.secp128r1, self.base)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0))

        mult = WindowNAFMultiplier(*formulas[:3], width, *formulas[3:],
                                   precompute_negation=True)
        mult.init(self.secp128r1, self.base)
        res_precompute = mult.multiply(157 * 789)
        self.assertPointEquality(res_precompute, res, scale)

    @parameterized.expand(cartesian([
        ("10", 10),
        ("2355498743", 2355498743),
        ("325385790209017329644351321912443757746", 325385790209017329644351321912443757746)
    ], [
        ("add-1998-cmo", "dbl-1998-cmo"),
        ("add-2016-rcb", "dbl-2016-rcb")
    ]))
    def test_basic_multipliers(self, name, num, add, dbl):
        ltr = LTRMultiplier(self.coords.formulas[add],
                            self.coords.formulas[dbl], self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            ltr.multiply(1)
        ltr.init(self.secp128r1, self.base)
        res_ltr = ltr.multiply(num)
        rtl = RTLMultiplier(self.coords.formulas[add],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            rtl.multiply(1)
        rtl.init(self.secp128r1, self.base)
        res_rtl = rtl.multiply(num)
        self.assertEqual(res_ltr, res_rtl)

        ltr_always = LTRMultiplier(self.coords.formulas[add],
                                   self.coords.formulas[dbl], self.coords.formulas["z"],
                                   always=True)
        rtl_always = RTLMultiplier(self.coords.formulas[add],
                                   self.coords.formulas[dbl], self.coords.formulas["z"],
                                   always=True)
        ltr_always.init(self.secp128r1, self.base)
        rtl_always.init(self.secp128r1, self.base)
        res_ltr_always = ltr_always.multiply(num)
        res_rtl_always = rtl_always.multiply(num)
        self.assertEqual(res_ltr, res_ltr_always)
        self.assertEqual(res_rtl, res_rtl_always)

        bnaf = BinaryNAFMultiplier(self.coords.formulas[add],
                                   self.coords.formulas[dbl],
                                   self.coords.formulas["neg"], self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            bnaf.multiply(1)
        bnaf.init(self.secp128r1, self.base)
        res_bnaf = bnaf.multiply(num)
        self.assertEqual(res_bnaf, res_ltr)

        wnaf = WindowNAFMultiplier(self.coords.formulas[add],
                                   self.coords.formulas[dbl],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            wnaf.multiply(1)
        wnaf.init(self.secp128r1, self.base)
        res_wnaf = wnaf.multiply(num)
        self.assertEqual(res_wnaf, res_ltr)

        ladder = SimpleLadderMultiplier(self.coords.formulas[add],
                                        self.coords.formulas[dbl],
                                        self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            ladder.multiply(1)
        ladder.init(self.secp128r1, self.base)
        res_ladder = ladder.multiply(num)
        self.assertEqual(res_ladder, res_ltr)

        coron = CoronMultiplier(self.coords.formulas[add],
                                self.coords.formulas[dbl],
                                self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            coron.multiply(1)
        coron.init(self.secp128r1, self.base)
        res_coron = coron.multiply(num)
        self.assertEqual(res_coron, res_ltr)

    def test_init_fail(self):
        mult = DifferentialLadderMultiplier(self.coords25519.formulas["dadd-1987-m"],
                                            self.coords25519.formulas["dbl-1987-m"],
                                            self.coords25519.formulas["scale"])
        with self.assertRaises(ValueError):
            mult.init(self.secp128r1, self.base)

        with self.assertRaises(ValueError):
            LadderMultiplier(self.coords25519.formulas["ladd-1987-m"],
                             scl=self.coords25519.formulas["scale"], complete=False)
