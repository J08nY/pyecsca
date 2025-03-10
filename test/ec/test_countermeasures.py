import pytest

from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.countermeasures import GroupScalarRandomization, AdditiveSplitting, MultiplicativeSplitting, \
    EuclideanSplitting


@pytest.fixture(params=["add-1998-cmo-2", "add-2015-rcb"])
def add(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


@pytest.fixture(params=["dbl-1998-cmo-2", "dbl-2015-rcb"])
def dbl(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]

@pytest.fixture()
def mult(secp128r1, add, dbl):
    return LTRMultiplier(add, dbl, complete=False)

@pytest.mark.parametrize(
    "num", [325385790209017329644351321912443757746,
            123456789314159265358979323846264338327,
            987654321314159265358979323846264338327,
            786877845665557891354654531354008066400]
)
def test_group_scalar_rand(mult, secp128r1, num):
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    gsr = GroupScalarRandomization(mult)
    gsr.init(secp128r1, secp128r1.generator)
    masked = gsr.multiply(num)
    assert raw.equals(masked)

@pytest.mark.parametrize(
    "num", [325385790209017329644351321912443757746,
            123456789314159265358979323846264338327,
            987654321314159265358979323846264338327,
            786877845665557891354654531354008066400]
)
def test_additive_splitting(mult, secp128r1, num):
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    asplit = AdditiveSplitting(mult)
    asplit.init(secp128r1, secp128r1.generator)
    masked = asplit.multiply(num)
    assert raw.equals(masked)

@pytest.mark.parametrize(
    "num", [325385790209017329644351321912443757746,
            123456789314159265358979323846264338327,
            987654321314159265358979323846264338327,
            786877845665557891354654531354008066400]
)
def test_multiplicative_splitting(mult, secp128r1, num):
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    msplit = MultiplicativeSplitting(mult)
    msplit.init(secp128r1, secp128r1.generator)
    masked = msplit.multiply(num)
    assert raw.equals(masked)

@pytest.mark.parametrize(
    "num", [325385790209017329644351321912443757746,
            123456789314159265358979323846264338327,
            987654321314159265358979323846264338327,
            786877845665557891354654531354008066400]
)
def test_euclidean_splitting(mult, secp128r1, num):
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    esplit = EuclideanSplitting(mult)
    esplit.init(secp128r1, secp128r1.generator)
    masked = esplit.multiply(num)
    assert raw.equals(masked)