from unittest import TestCase

from pyecsca.ec.configuration import (all_configurations, HashType, RandomMod, Multiplication,
                                      Squaring, Reduction, Inversion)
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import LTRMultiplier
from .utils import slow


class ConfigurationTests(TestCase):

    def base_independents(self):
        return {
            "hash_type": HashType.SHA1,
            "mod_rand": RandomMod.SAMPLE,
            "mult": Multiplication.BASE,
            "sqr": Squaring.BASE,
            "red": Reduction.BASE,
            "inv": Inversion.GCD
        }

    @slow
    def test_all(self):
        j = 0
        for _ in all_configurations(model=ShortWeierstrassModel()):
            j += 1
        print(j)

    def test_weierstrass_projective(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        configs = list(all_configurations(model=model, coords=coords, **self.base_independents()))
        self.assertEqual(len(configs), 1960)

    def test_mult_class(self):
        model = ShortWeierstrassModel()
        coords = model.coordinates["projective"]
        scalarmult = LTRMultiplier
        configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult,
                                          **self.base_independents()))
        self.assertEqual(len(configs), 560)

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
        configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult,
                                          **self.base_independents()))
        self.assertEqual(len(configs), 1)
        scalarmult = LTRMultiplier(coords.formulas["add-1998-cmo"], coords.formulas["dbl-1998-cmo"],
                                   None, True, False, True)
        configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult,
                                          **self.base_independents()))
        self.assertEqual(len(configs), 1)
        configs = list(all_configurations(model=model, scalarmult=scalarmult,
                                          **self.base_independents()))
        self.assertEqual(len(configs), 1)
