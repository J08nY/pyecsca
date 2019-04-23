from unittest import TestCase

from pyecsca.ec.context import local, DefaultContext
from pyecsca.ec.mult import LTRMultiplier
from test.ec.curves import get_secp128r1


class ContextTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_secp128r1()
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.mult = LTRMultiplier(self.secp128r1, self.coords.formulas["add-1998-cmo"],
                                  self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])

    def test_null(self):
        self.mult.multiply(59, self.base)

    def test_default(self):
        with local(DefaultContext()) as ctx:
            self.mult.multiply(59, self.base)
        self.assertEqual(len(ctx.actions), 10)
