from unittest import TestCase

from pyecsca.ec.model import (
    ShortWeierstrassModel,
    MontgomeryModel,
    EdwardsModel,
    TwistedEdwardsModel,
)


class CurveModelTests(TestCase):
    def test_load(self):
        self.assertGreater(len(ShortWeierstrassModel().coordinates), 0)
        self.assertGreater(len(MontgomeryModel().coordinates), 0)
        self.assertGreater(len(EdwardsModel().coordinates), 0)
        self.assertGreater(len(TwistedEdwardsModel().coordinates), 0)
