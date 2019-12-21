import ast
from unittest import TestCase

from pyecsca.ec.context import (local, DefaultContext, OpResult, NullContext, getcontext,
                                setcontext,
                                resetcontext)
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curves import get_curve
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.point import Point


class OpResultTests(TestCase):

    def test_str(self):
        for op, char in zip((ast.Add(), ast.Sub(), ast.Mult(), ast.Div()), "+-*/"):
            res = OpResult("X1", Mod(0, 5), op, Mod(2, 5), Mod(3, 5))
            self.assertEqual(str(res), "X1")


class ContextTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_curve("secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                  self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])

    def test_null(self):
        with local() as ctx:
            self.mult.multiply(59, self.base)
        self.assertIsInstance(ctx, NullContext)

    def test_default(self):
        token = setcontext(DefaultContext())
        self.addCleanup(resetcontext, token)

        with local(DefaultContext()) as ctx:
            self.mult.multiply(59, self.base)
        self.assertEqual(len(ctx.actions), 10)
        self.assertEqual(len(getcontext().actions), 0)

    def test_execute(self):
        with self.assertRaises(ValueError):
            getcontext().execute(self.coords.formulas["z"], self.base, self.base)
        with self.assertRaises(ValueError):
            getcontext().execute(self.coords.formulas["z"],
                                 Point(AffineCoordinateModel(self.secp128r1.curve.model),
                                       x=Mod(1, 5), y=Mod(2, 5)))

    def test_str(self):
        with local(DefaultContext()) as default:
            self.mult.multiply(59, self.base)
        str(default)
        str(default.actions)
        with local(NullContext()) as null:
            self.mult.multiply(59, self.base)
        str(null)
