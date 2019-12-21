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

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_rtl(self, name, add, dbl, scale):
        mult = RTLMultiplier(self.secp128r1, *self.get_formulas(self.coords, add, dbl, scale))
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_ltr(self, name, add, dbl, scale):
        mult = LTRMultiplier(self.secp128r1, *self.get_formulas(self.coords, add, dbl, scale))
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_coron(self, name, add, dbl, scale):
        mult = CoronMultiplier(self.secp128r1, *self.get_formulas(self.coords, add, dbl, scale))
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    def test_ladder(self):
        mult = LadderMultiplier(self.curve25519, self.coords25519.formulas["ladd-1987-m"],
                                self.coords25519.formulas["dbl-1987-m"],
                                self.coords25519.formulas["scale"])
        res = mult.multiply(15, self.base25519)
        other = mult.multiply(5, self.base25519)
        other = mult.multiply(3, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords25519), mult.multiply(0, self.base25519))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", None)
    ])
    def test_simple_ladder(self, name, add, dbl, scale):
        mult = SimpleLadderMultiplier(self.secp128r1,
                                      *self.get_formulas(self.coords, add, dbl, scale))
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    @parameterized.expand([
        ("10", 15),
        ("2355498743", 2355498743,)
    ])
    def test_ladder_differential(self, name, num):
        ladder = LadderMultiplier(self.curve25519, self.coords25519.formulas["ladd-1987-m"],
                                  self.coords25519.formulas["dbl-1987-m"],
                                  self.coords25519.formulas["scale"])
        differential = SimpleLadderMultiplier(self.curve25519,
                                              self.coords25519.formulas["dadd-1987-m"],
                                              self.coords25519.formulas["dbl-1987-m"],
                                              self.coords25519.formulas["scale"])
        res_ladder = ladder.multiply(num, self.base25519)
        res_differential = differential.multiply(num, self.base25519)
        self.assertEqual(res_ladder, res_differential)
        self.assertEqual(InfinityPoint(self.coords25519), differential.multiply(0, self.base25519))

    @parameterized.expand([
        ("scaled", "add-1998-cmo", "dbl-1998-cmo", "neg", "z"),
        ("none", "add-1998-cmo", "dbl-1998-cmo", "neg", None)
    ])
    def test_binary_naf(self, name, add, dbl, neg, scale):
        mult = BinaryNAFMultiplier(self.secp128r1,
                                   *self.get_formulas(self.coords, add, dbl, neg, scale))
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    @parameterized.expand([
        ("scaled3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, "z"),
        ("none3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, None)
    ])
    def test_window_naf(self, name, add, dbl, neg, width, scale):
        formulas = self.get_formulas(self.coords, add, dbl, neg, scale)
        mult = WindowNAFMultiplier(self.secp128r1, *formulas[:3], width, *formulas[3:])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertPointEquality(res, other, scale)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

        mult = WindowNAFMultiplier(self.secp128r1, *formulas[:3], width, *formulas[3:],
                                   precompute_negation=True)
        res_precompute = mult.multiply(10, self.base)
        self.assertPointEquality(res_precompute, res, scale)

    @parameterized.expand([
        ("10", 10),
        ("2355498743", 2355498743,)
    ])
    def test_basic_multipliers(self, name, num):
        ltr = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_ltr = ltr.multiply(num, self.base)
        rtl = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_rtl = rtl.multiply(num, self.base)
        self.assertEqual(res_ltr, res_rtl)

        ltr_always = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        rtl_always = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        res_ltr_always = ltr_always.multiply(num, self.base)
        res_rtl_always = rtl_always.multiply(num, self.base)
        self.assertEqual(res_ltr, res_ltr_always)
        self.assertEqual(res_rtl, res_rtl_always)

        bnaf = BinaryNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], self.coords.formulas["z"])
        res_bnaf = bnaf.multiply(num, self.base)
        self.assertEqual(res_bnaf, res_ltr)

        wnaf = WindowNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"])
        res_wnaf = wnaf.multiply(num, self.base)
        self.assertEqual(res_wnaf, res_ltr)

        ladder = SimpleLadderMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                        self.coords.formulas["dbl-1998-cmo"],
                                        self.coords.formulas["z"])
        res_ladder = ladder.multiply(num, self.base)
        self.assertEqual(res_ladder, res_ltr)

        coron = CoronMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                self.coords.formulas["dbl-1998-cmo"],
                                self.coords.formulas["z"])
        res_coron = coron.multiply(num, self.base)
        self.assertEqual(res_coron, res_ltr)

    def test_init_fail(self):
        with self.assertRaises(ValueError):
            SimpleLadderMultiplier(self.secp128r1,
                                   self.coords25519.formulas["dadd-1987-m"],
                                   self.coords25519.formulas["dbl-1987-m"],
                                   self.coords25519.formulas["scale"])

    def test_mult_fail(self):
        mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        with self.assertRaises(ValueError):
            mult.multiply(15)
