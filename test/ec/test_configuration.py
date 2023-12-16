import pickle

import pytest

from pyecsca.ec.configuration import (
    all_configurations,
    HashType,
    RandomMod,
    Multiplication,
    Squaring,
    Reduction,
    Inversion,
)
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import LTRMultiplier, AccumulationOrder


@pytest.fixture(scope="module")
def base_independents():
    return {"hash_type": HashType.SHA1, "mod_rand": RandomMod.SAMPLE, "mult": Multiplication.BASE, "sqr": Squaring.BASE,
            "red": Reduction.BASE, "inv": Inversion.GCD, }


@pytest.mark.slow
def test_all():
    j = 0
    for _ in all_configurations(model=ShortWeierstrassModel()):
        j += 1


def test_weierstrass_projective(base_independents):
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    configs = list(all_configurations(model=model, coords=coords, **base_independents))
    assert len(set(map(lambda cfg: cfg.scalarmult, configs))) == len(configs)
    assert len(configs) == 19040


def test_mult_class(base_independents):
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    scalarmult = LTRMultiplier
    configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult, **base_independents))
    assert len(set(map(lambda cfg: cfg.scalarmult, configs))) == len(configs)
    assert len(configs) == 1280


def test_one(base_independents):
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    scalarmult = {"cls": LTRMultiplier, "add": coords.formulas["add-1998-cmo"], "dbl": coords.formulas["dbl-1998-cmo"],
                  "scl": None, "always": True, "complete": False, "short_circuit": True,
                  "accumulation_order": AccumulationOrder.PeqRP}
    configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult, **base_independents))
    assert len(configs) == 1
    scalarmult = LTRMultiplier(coords.formulas["add-1998-cmo"], coords.formulas["dbl-1998-cmo"], None, True,
                               accumulation_order=AccumulationOrder.PeqRP, complete=False, short_circuit=True)
    configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult, **base_independents))
    assert len(configs) == 1
    configs = list(all_configurations(model=model, scalarmult=scalarmult, **base_independents))
    assert len(configs) == 1


def test_pickle(base_independents):
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    scalarmult = {"cls": LTRMultiplier, "add": coords.formulas["add-1998-cmo"], "dbl": coords.formulas["dbl-1998-cmo"],
                  "scl": None, "always": True, "complete": False, "short_circuit": True,
                  "accumulation_order": AccumulationOrder.PeqRP}
    configs = list(all_configurations(model=model, coords=coords, scalarmult=scalarmult, **base_independents))
    config = configs[0]
    assert config == pickle.loads(pickle.dumps(config))
