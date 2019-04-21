from unittest import TestCase

from pyecsca.ec.mult import (LTRMultiplier, RTLMultiplier, LadderMultiplier, BinaryNAFMultiplier,
                             WindowNAFMultiplier, SimpleLadderMultiplier, CoronMultiplier)
from pyecsca.ec.point import InfinityPoint
from test.ec.curves import get_secp128r1, get_curve25519


class ScalarMultiplierTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model

        self.curve25519 = get_curve25519()
        self.base25519 = self.curve25519.generator
        self.coords25519 = self.curve25519.curve.coordinate_model

    def test_rtl(self):
        mult = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    def test_ltr(self):
        mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                             self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    def test_coron(self):
        mult = CoronMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                               self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
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

    def test_simple_ladder(self):
        mult = SimpleLadderMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                      self.coords.formulas["dbl-1998-cmo"],
                                      self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    def test_ladder_differential(self):
        ladder = LadderMultiplier(self.curve25519, self.coords25519.formulas["ladd-1987-m"],
                                  self.coords25519.formulas["dbl-1987-m"],
                                  self.coords25519.formulas["scale"])
        differential = SimpleLadderMultiplier(self.curve25519,
                                              self.coords25519.formulas["dadd-1987-m"],
                                              self.coords25519.formulas["dbl-1987-m"],
                                              self.coords25519.formulas["scale"])
        res_ladder = ladder.multiply(15, self.base25519)
        res_differential = differential.multiply(15, self.base25519)
        self.assertEqual(res_ladder, res_differential)
        self.assertEqual(InfinityPoint(self.coords25519), differential.multiply(0, self.base25519))

    def test_binary_naf(self):
        mult = BinaryNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

    def test_window_naf(self):
        mult = WindowNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"])
        res = mult.multiply(10, self.base)
        other = mult.multiply(5, self.base)
        other = mult.multiply(2, other)
        self.assertEqual(res, other)
        self.assertEqual(InfinityPoint(self.coords), mult.multiply(0, self.base))

        mult = WindowNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"],
                                   precompute_negation=True)
        res_precompute = mult.multiply(10, self.base)
        self.assertEqual(res_precompute, res)

    def test_basic_multipliers(self):
        ltr = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_ltr = ltr.multiply(10, self.base)
        rtl = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                            self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        res_rtl = rtl.multiply(10, self.base)
        self.assertEqual(res_ltr, res_rtl)

        ltr_always = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        rtl_always = RTLMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"],
                                   always=True)
        res_ltr_always = ltr_always.multiply(10, self.base)
        res_rtl_always = rtl_always.multiply(10, self.base)
        self.assertEqual(res_ltr, res_ltr_always)
        self.assertEqual(res_rtl, res_rtl_always)

        bnaf = BinaryNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], self.coords.formulas["z"])
        res_bnaf = bnaf.multiply(10, self.base)
        self.assertEqual(res_bnaf, res_ltr)

        wnaf = WindowNAFMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                   self.coords.formulas["dbl-1998-cmo"],
                                   self.coords.formulas["neg"], 3, self.coords.formulas["z"])
        res_wnaf = wnaf.multiply(10, self.base)
        self.assertEqual(res_wnaf, res_ltr)

        ladder = SimpleLadderMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                        self.coords.formulas["dbl-1998-cmo"],
                                        self.coords.formulas["z"])
        res_ladder = ladder.multiply(10, self.base)
        self.assertEqual(res_ladder, res_ltr)

        coron = CoronMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                self.coords.formulas["dbl-1998-cmo"],
                                self.coords.formulas["z"])
        res_coron = coron.multiply(10, self.base)
        self.assertEqual(res_coron, res_ltr)
