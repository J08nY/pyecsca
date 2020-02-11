from unittest import TestCase

from pyecsca.ec.context import (local, DefaultContext, NullContext, getcontext,
                                setcontext, resetcontext)
from pyecsca.ec.curves import get_params
from pyecsca.ec.mult import LTRMultiplier, ScalarMultiplicationAction


class ContextTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.mult = LTRMultiplier(self.coords.formulas["add-1998-cmo"],
                                  self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        self.mult.init(self.secp128r1, self.base)

    def test_null(self):
        with local() as ctx:
            self.mult.multiply(59)
        self.assertIsInstance(ctx, NullContext)

    def test_default(self):
        token = setcontext(DefaultContext())
        self.addCleanup(resetcontext, token)

        with local(DefaultContext()) as ctx:
            self.mult.multiply(59)
        self.assertEqual(len(ctx.actions), 1)
        self.assertIsInstance(next(iter(ctx.actions.keys())), ScalarMultiplicationAction)
        self.assertEqual(len(getcontext().actions), 0)

    def test_str(self):
        with local(DefaultContext()) as default:
            self.mult.multiply(59)
        str(default)
        str(default.actions)
        with local(NullContext()) as null:
            self.mult.multiply(59)
        str(null)
