from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.curves import get_curve
from pyecsca.ec.mult import (LTRMultiplier, RTLMultiplier, LadderMultiplier, BinaryNAFMultiplier,
                             WindowNAFMultiplier, SimpleLadderMultiplier, CoronMultiplier)
from pyecsca.ec.point import InfinityPoint


class ScalarMultiplierTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_curve("secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model

        self.curve25519 = get_curve("curve25519", "xz")
        self.base25519 = self.curve25519.generator
        self.coords25519 = self.curve25519.curve.coordinate_model

    def get_formulas(self, coords, *names):
        return [coords.formulas[name] for name in names if name is not None]

    def assertPointEquality(self, one, other, scale):
        if scale:
            self.assertEqual(one, other)
        else:
            assert one.equals(other)

    def do_basic_test(self, mult_class, group, base, add, dbl, scale, neg=None):
        mult = mult_class(*self.get_formulas(group.curve.coordinate_model, add, dbl, neg, scale))
        mult.init(group, base)
        res = mult.multiply(314)
        other = mult.multiply(157)
        mult.init(group, other)
        other = mult.multiply(2)
        self.assertPointEquality(res, other, scale)
        mult.init(group, base)
        self.assertEqual(InfinityPoint(group.curve.coordinate_model), mult.multiply(0))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_rtl(self, name, add, dbl, scale):
        self.do_basic_test(RTLMultiplier, self.secp128r1, self.base, add, dbl, scale)

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_ltr(self, name, add, dbl, scale):
        self.do_basic_test(LTRMultiplier, self.secp128r1, self.base, add, dbl, scale)

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_coron(self, name, add, dbl, scale):
        self.do_basic_test(CoronMultiplier, self.secp128r1, self.base, add, dbl, scale)

    def test_ladder(self):
        self.do_basic_test(LadderMultiplier, self.curve25519, self.base25519, "ladd-1987-m",
                           "dbl-1987-m", "scale")

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_simple_ladder(self, name, add, dbl, scale):
        self.do_basic_test(SimpleLadderMultiplier, self.secp128r1, self.base, add, dbl, scale)

    @parameterized.expand([
        ("10", 15),
        ("2355498743", 2355498743,)
    ])
    def test_ladder_differential(self, name, num):
        ladder = LadderMultiplier(self.coords25519.formulas["ladd-1987-m"],
                                  self.coords25519.formulas["dbl-1987-m"],
                                  self.coords25519.formulas["scale"])
        differential = SimpleLadderMultiplier(self.coords25519.formulas["dadd-1987-m"],
                                              self.coords25519.formulas["dbl-1987-m"],
                                              self.coords25519.formulas["scale"])
        ladder.init(self.curve25519, self.base25519)
        res_ladder = ladder.multiply(num)
        differential.init(self.curve25519, self.base25519)
        res_differential = differential.multiply(num)
        self.assertEqual(res_ladder, res_differential)
        self.assertEqual(InfinityPoint(self.coords25519), differential.multiply(0))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "neg", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", "neg", None)
    ])
    def test_binary_naf(self, name, add, dbl, neg, scale):
        self.do_basic_test(BinaryNAFMultiplier, self.secp128r1, self.base, add, dbl, scale, neg)

    @parameterized.expand([
        ("scaled3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, "z"),
        ("none3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, None)
    ])
    def test_window_naf(self, name, add, dbl, neg, width, scale):
        formulas = self.get_formulas(self.coords, add, dbl, neg, scale)
        mult = WindowNAFMultiplier(*formulas[:3], width, *formulas[3:])
        mult.init(self.secp128r1, self.base)
        res = mult.multiply(10)
        other = mult.multiply(5)
        mult.init(self.secp128r1, other)
        other = mult.multiply(2)
        self.assertPointEquality(res, other, scale)
        mult.init(self.secp128r1, self.base)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0))

        mult = WindowNAFMultiplier(*formulas[:3], width, *formulas[3:],
                                   precompute_negation=True)
        mult.init(self.secp128r1, self.base)
        res_precompute = mult.multiply(10)
        self.assertPointEquality(res_precompute, res, scale)

    @parameterized.expand([
        ("10", 10),
        ("2355498743", 2355498743,)
    ])
    def test_basic_multipliers(self, name, num):
        ltr = LTRMultiplier(self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        ltr.init(self.secp128r1, self.base)
        res_ltr = ltr.multiply(num)
        rtl = RTLMultiplier(self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        rtl.init(self.secp128r1, self.base)
        res_rtl = rtl.multiply(num)
        self.assertEqual(res_ltr, res_rtl)

        ltr_always = LTRMultiplier(self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        rtl_always = RTLMultiplier(self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        ltr_always.init(self.secp128r1, self.base)
        rtl_always.init(self.secp128r1, self.base)
        res_ltr_always = ltr_always.multiply(num)
        res_rtl_always = rtl_always.multiply(num)
        self.assertEqual(res_ltr, res_ltr_always)
        self.assertEqual(res_rtl, res_rtl_always)

        bnaf = BinaryNAFMultiplier(self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], self.coords.formulas["z"])
        bnaf.init(self.secp128r1, self.base)
        res_bnaf = bnaf.multiply(num)
        self.assertEqual(res_bnaf, res_ltr)

        wnaf = WindowNAFMultiplier(self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"])
        wnaf.init(self.secp128r1, self.base)
        res_wnaf = wnaf.multiply(num)
        self.assertEqual(res_wnaf, res_ltr)

        ladder = SimpleLadderMultiplier(self.coords.formulas["add-1998-cmo"],
                                        self.coords.formulas["dbl-1998-cmo"],
                                        self.coords.formulas["z"])
        ladder.init(self.secp128r1, self.base)
        res_ladder = ladder.multiply(num)
        self.assertEqual(res_ladder, res_ltr)

        coron = CoronMultiplier(self.coords.formulas["add-1998-cmo"],
                                self.coords.formulas["dbl-1998-cmo"],
                                self.coords.formulas["z"])
        coron.init(self.secp128r1, self.base)
        res_coron = coron.multiply(num)
        self.assertEqual(res_coron, res_ltr)

    def test_init_fail(self):
        mult = SimpleLadderMultiplier(self.coords25519.formulas["dadd-1987-m"],
                                      self.coords25519.formulas["dbl-1987-m"],
                                      self.coords25519.formulas["scale"])
        with self.assertRaises(ValueError):
            mult.init(self.secp128r1, self.base)
