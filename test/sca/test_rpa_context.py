from typing import cast

import pytest

from pyecsca.ec.context import local
from pyecsca.ec.formula import LadderFormula, DifferentialAdditionFormula, DoublingFormula, \
    ScalingFormula
from pyecsca.ec.mult import (
    LTRMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    LadderMultiplier,
    DifferentialLadderMultiplier
)
from pyecsca.sca.re.rpa import MultipleContext


@pytest.fixture()
def add(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["add-1998-cmo"]


@pytest.fixture()
def dbl(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["dbl-1998-cmo"]


@pytest.fixture()
def neg(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["neg"]


@pytest.fixture()
def scale(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["z"]


@pytest.mark.parametrize("name,scalar",
                         [
                             ("5", 5),
                             ("10", 10),
                             ("2355498743", 2355498743),
                             (
                                     "325385790209017329644351321912443757746",
                                     325385790209017329644351321912443757746,
                             ),
                             ("13613624287328732", 13613624287328732),
                         ])
def test_basic(secp128r1, add, dbl, scale, name, scalar):
    mult = LTRMultiplier(
        add,
        dbl,
        scale,
        always=False,
        complete=False,
        short_circuit=True,
    )
    with local(MultipleContext()) as ctx:
        mult.init(secp128r1, secp128r1.generator)
        mult.multiply(scalar)
    muls = list(ctx.points.values())
    assert muls[-1] == scalar


def test_precomp(secp128r1, add, dbl, neg, scale):
    bnaf = BinaryNAFMultiplier(add, dbl, neg, scale)
    with local(MultipleContext()) as ctx:
        bnaf.init(secp128r1, secp128r1.generator)
    muls = list(ctx.points.values())
    assert muls == [1, -1]

    wnaf = WindowNAFMultiplier(add, dbl, neg, 3, scale)
    with local(MultipleContext()) as ctx:
        wnaf.init(secp128r1, secp128r1.generator)
    muls = list(ctx.points.values())
    assert muls == [1, 2, 3, 5]


def test_window(secp128r1, add, dbl, neg):
    mult = WindowNAFMultiplier(
        add, dbl, neg, 3, precompute_negation=True
    )
    with local(MultipleContext()):
        mult.init(secp128r1, secp128r1.generator)
        mult.multiply(5)


def test_ladder(curve25519):
    base = curve25519.generator
    coords = curve25519.curve.coordinate_model
    ladd = cast(LadderFormula, coords.formulas["ladd-1987-m"])
    dadd = cast(DifferentialAdditionFormula, coords.formulas["dadd-1987-m"])
    dbl = cast(DoublingFormula, coords.formulas["dbl-1987-m"])
    scale = cast(ScalingFormula, coords.formulas["scale"])
    ladd_mult = LadderMultiplier(ladd, dbl, scale)
    with local(MultipleContext()) as ctx:
        ladd_mult.init(curve25519, base)
        ladd_mult.multiply(1339278426732672313)
    muls = list(ctx.points.values())
    assert muls[-2] == 1339278426732672313
    dadd_mult = DifferentialLadderMultiplier(dadd, dbl, scale)
    with local(MultipleContext()) as ctx:
        dadd_mult.init(curve25519, base)
        dadd_mult.multiply(1339278426732672313)
    muls = list(ctx.points.values())
    assert muls[-2] == 1339278426732672313
