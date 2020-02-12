from unittest import TestCase

from pyecsca.ec.configuration import (all_configurations, HashType, RandomMod, Multiplication,
                                      Squaring, Reduction)
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import LTRMultiplier
from test.sca.utils import slow


class ConfigurationTests(TestCase):

    @slow
    def test_all(self):
        j = 0
        for _ in all_configurations(model=ShortWeierstrassModel()):
            j += 1
        print(j)

    def test_mult_class(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        scalarmult = LTRMultiplier
        hash_type = HashType.SHA1
        mod_rand = RandomMod.SAMPLE
        mult = Multiplication.BASE
        sqr = Squaring.BASE
        red = Reduction.BASE
        configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult,
                                          hash_type=hash_type, mod_rand=mod_rand, mult=mult,
                                          sqr=sqr, red=red))
        self.assertEqual(len(configs), 384)

    def test_one(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        scalarmult = {
            "cls": LTRMultiplier,
            "add": coords.formulas["add-1998-cmo"],
            "dbl": coords.formulas["dbl-1998-cmo"],
            "scl": None,
            "always": True,
            "complete": False,
            "short_circuit": True
        }
        hash_type = HashType.SHA1
        mod_rand = RandomMod.SAMPLE
        mult = Multiplication.BASE
        sqr = Squaring.BASE
        red = Reduction.BASE
        configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult,
                                          hash_type=hash_type, mod_rand=mod_rand, mult=mult,
                                          sqr=sqr, red=red))
        self.assertEqual(len(configs), 1)
