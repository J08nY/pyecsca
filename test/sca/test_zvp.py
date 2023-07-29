from unittest import TestCase

from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.sca.re.zvp import unroll_formula


class ZVPTests(TestCase):
    def setUp(self):
        self.model = ShortWeierstrassModel()
        self.coords = self.model.coordinates["projective"]
        self.add = self.coords.formulas["add-2007-bl"]
        self.dbl = self.coords.formulas["dbl-2007-bl"]
        self.neg = self.coords.formulas["neg"]

    def test_unroll(self):
        results = unroll_formula(self.add, 11)
        self.assertIsNotNone(results)
        results = unroll_formula(self.dbl, 11)
        self.assertIsNotNone(results)
        results = unroll_formula(self.neg, 11)
        self.assertIsNotNone(results)
