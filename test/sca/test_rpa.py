from functools import partial
from math import isqrt

import pytest

from pyecsca.ec.context import local
from pyecsca.ec.countermeasures import AdditiveSplitting
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SimpleLadderMultiplier,
    AccumulationOrder,
    ProcessingDirection,
    SlidingWindowMultiplier,
    FixedWindowLTRMultiplier,
    FullPrecompMultiplier,
    BGMWMultiplier,
    CombMultiplier,
    WindowBoothMultiplier,
    LadderMultiplier,
    DifferentialLadderMultiplier,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import (
    MultipleContext,
    rpa_point_0y,
    rpa_point_x0,
    rpa_distinguish,
    multiples_computed,
)


@pytest.fixture()
def model():
    return ShortWeierstrassModel()


@pytest.fixture()
def coords(model):
    return model.coordinates["projective"]


@pytest.fixture()
def add(coords):
    return coords.formulas["add-2007-bl"]


@pytest.fixture()
def dbl(coords):
    return coords.formulas["dbl-2007-bl"]


@pytest.fixture()
def neg(coords):
    return coords.formulas["neg"]


@pytest.fixture()
def rpa_params(model, coords):
    p = 0x85D265945A4F5681
    a = mod(0x7FC57B4110698BC0, p)
    b = mod(0x37113EA591B04527, p)
    gx = mod(0x80D2D78FDDB97597, p)
    gy = mod(0x5586D818B7910930, p)

    infty = Point(coords, X=mod(0, p), Y=mod(1, p), Z=mod(0, p))
    g = Point(coords, X=gx, Y=gy, Z=mod(1, p))
    curve = EllipticCurve(model, coords, p, infty, dict(a=a, b=b))
    return DomainParameters(curve, g, 0x85D265932D90785C, 1)


def test_multiples(rpa_params):
    multiples = multiples_computed(
        17, rpa_params, LTRMultiplier, LTRMultiplier, True, True
    )
    assert multiples == {1, 2, 4, 8, 16, 17}


def test_multiples_no_init(rpa_params):
    multiples = multiples_computed(
        78699, rpa_params, LTRMultiplier,
        lambda add, dbl, *args, **kwargs: LTRMultiplier(
            add, dbl, None, False, AccumulationOrder.PeqPR, True, False
        ), False, True
    )
    assert multiples


def test_multiples_bnaf(rpa_params):
    mult_partial = partial(BinaryNAFMultiplier, always=True, direction=ProcessingDirection.LTR)
    multiples = multiples_computed(
        199, rpa_params, BinaryNAFMultiplier, mult_partial, True, True,
        kind="all"
    )
    assert 23 in multiples
    assert 199 in multiples


def test_multiples_kind(rpa_params):
    multiples_all = multiples_computed(
        17, rpa_params, RTLMultiplier, RTLMultiplier, True, True,
        kind="all"
    )
    multiples_input = multiples_computed(
        17, rpa_params, RTLMultiplier, RTLMultiplier, True, True,
        kind="input"
    )
    multiples_necessary = multiples_computed(
        17, rpa_params, RTLMultiplier, RTLMultiplier, True, True,
        kind="necessary"
    )
    multiples_precomp = multiples_computed(
        17, rpa_params, RTLMultiplier, RTLMultiplier, True, True,
        kind="precomp+necessary"
    )
    assert multiples_all != multiples_input
    assert multiples_all != multiples_necessary
    assert multiples_input != multiples_necessary
    assert multiples_precomp == multiples_necessary

    wnaf = partial(WindowNAFMultiplier, width=4)
    multiples_all = multiples_computed(
        0xff, rpa_params, WindowNAFMultiplier, wnaf, True, True,
        kind="all"
    )
    multiples_input = multiples_computed(
        0xff, rpa_params, WindowNAFMultiplier, wnaf, True, True,
        kind="input"
    )
    multiples_necessary = multiples_computed(
        0xff, rpa_params, WindowNAFMultiplier, wnaf, True, True,
        kind="necessary"
    )
    multiples_precomp = multiples_computed(
        0xff, rpa_params, WindowNAFMultiplier, wnaf, True, True,
        kind="precomp+necessary"
    )
    assert multiples_all != multiples_input
    assert multiples_all != multiples_necessary
    assert multiples_input != multiples_necessary
    assert multiples_precomp != multiples_necessary


def test_multiples_additive(rpa_params):
    mults = multiples_computed(1454656138887897564, rpa_params, LTRMultiplier, lambda *args, **kwargs: AdditiveSplitting(LTRMultiplier(*args, **kwargs)), True, True, kind="precomp+necessary")
    assert mults is not None


def test_x0_point(rpa_params):
    res = rpa_point_x0(rpa_params)
    assert res is not None
    assert res.y == 0


def test_0y_point(rpa_params):
    res = rpa_point_0y(rpa_params)
    assert res is not None
    assert res.x == 0


@pytest.fixture()
def distinguish_params_sw(model, coords):
    p = 0xCB5E1D94A6168511
    a = mod(0xB166CA7D2DFBF69F, p)
    b = mod(0x855BB40CB6937C4B, p)
    gx = mod(0x253B2638BD13D6F4, p)
    gy = mod(0x1E91A1A182287E71, p)

    infty = Point(coords, X=mod(0, p), Y=mod(1, p), Z=mod(0, p))
    g = Point(coords, X=gx, Y=gy, Z=mod(1, p))
    curve = EllipticCurve(model, coords, p, infty, dict(a=a, b=b))
    return DomainParameters(curve, g, 0xCB5E1D94601A3AC5, 1)


def test_distinguish_basic(distinguish_params_sw, add, dbl, neg):
    multipliers = [
        LTRMultiplier(add, dbl, None, False, AccumulationOrder.PeqPR, True, True),
        LTRMultiplier(add, dbl, None, True, AccumulationOrder.PeqPR, True, True),
        RTLMultiplier(add, dbl, None, False, AccumulationOrder.PeqPR, True),
        RTLMultiplier(add, dbl, None, True, AccumulationOrder.PeqPR, False),
        SimpleLadderMultiplier(add, dbl, None, True, True),
        BinaryNAFMultiplier(
            add, dbl, neg, None, False, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        BinaryNAFMultiplier(
            add, dbl, neg, None, False, ProcessingDirection.RTL, AccumulationOrder.PeqPR, True
        ),
        WindowNAFMultiplier(
            add, dbl, neg, 3, None, AccumulationOrder.PeqPR, True, True
        ),
        WindowNAFMultiplier(
            add, dbl, neg, 4, None, AccumulationOrder.PeqPR, True, True
        ),
        WindowNAFMultiplier(
            add, dbl, neg, 5, None, AccumulationOrder.PeqPR, True, True
        ),
        WindowBoothMultiplier(
            add, dbl, neg, 3, None, AccumulationOrder.PeqPR, True, True
        ),
        WindowBoothMultiplier(
            add, dbl, neg, 4, None, AccumulationOrder.PeqPR, True, True
        ),
        WindowBoothMultiplier(
            add, dbl, neg, 5, None, AccumulationOrder.PeqPR, True, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 3, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 4, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 5, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 3, None, ProcessingDirection.RTL, AccumulationOrder.PeqPR, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 4, None, ProcessingDirection.RTL, AccumulationOrder.PeqPR, True
        ),
        SlidingWindowMultiplier(
            add, dbl, 5, None, ProcessingDirection.RTL, AccumulationOrder.PeqPR, True
        ),
        FixedWindowLTRMultiplier(add, dbl, 3, None, AccumulationOrder.PeqPR, True),
        FixedWindowLTRMultiplier(add, dbl, 4, None, AccumulationOrder.PeqPR, True),
        FixedWindowLTRMultiplier(add, dbl, 5, None, AccumulationOrder.PeqPR, True),
        FixedWindowLTRMultiplier(add, dbl, 8, None, AccumulationOrder.PeqPR, True),
        FixedWindowLTRMultiplier(add, dbl, 16, None, AccumulationOrder.PeqPR, True),
        FullPrecompMultiplier(
            add,
            dbl,
            None,
            True,
            ProcessingDirection.LTR,
            AccumulationOrder.PeqPR,
            True,
            True,
        ),
        FullPrecompMultiplier(
            add,
            dbl,
            None,
            False,
            ProcessingDirection.LTR,
            AccumulationOrder.PeqPR,
            True,
            True,
        ),
        BGMWMultiplier(
            add, dbl, 2, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        BGMWMultiplier(
            add, dbl, 3, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        BGMWMultiplier(
            add, dbl, 4, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        BGMWMultiplier(
            add, dbl, 5, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        CombMultiplier(add, dbl, 2, None, False, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 3, None, False, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 4, None, False, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 5, None, False, AccumulationOrder.PeqPR, True),
    ]
    for real_mult in multipliers:

        def simulated_oracle(scalar, affine_point):
            point = affine_point.to_model(
                distinguish_params_sw.curve.coordinate_model,
                distinguish_params_sw.curve,
            )
            with local(MultipleContext()) as ctx:
                real_mult.init(distinguish_params_sw, point)
                real_mult.multiply(scalar)
            return any(
                map(lambda P: P.X == 0 or P.Y == 0, sum(ctx.parents.values(), []))
            )

        result = rpa_distinguish(distinguish_params_sw, multipliers, simulated_oracle)
        assert real_mult in result
        assert 1 == len(result)


def test_distinguish_ladders(curve25519):
    ladd = curve25519.curve.coordinate_model.formulas["ladd-1987-m"]
    dbl = curve25519.curve.coordinate_model.formulas["dbl-1987-m"]
    dadd = curve25519.curve.coordinate_model.formulas["dadd-1987-m"]

    multipliers = [
        LadderMultiplier(ladd, None, None, True, False, False),
        LadderMultiplier(ladd, dbl, None, False, False, False),
        LadderMultiplier(ladd, None, None, False, False, True),
        DifferentialLadderMultiplier(dadd, dbl, None, True, False, False),
        DifferentialLadderMultiplier(dadd, dbl, None, False, False, True),
        DifferentialLadderMultiplier(dadd, dbl, None, False, False, False),
    ]
    for real_mult in multipliers:

        def simulated_oracle(scalar, affine_point):
            point = affine_point.to_model(
                curve25519.curve.coordinate_model, curve25519.curve
            )
            with local(MultipleContext()) as ctx:
                real_mult.init(curve25519, point)
                real_mult.multiply(scalar)
            return any(map(lambda P: P.X == 0, sum(ctx.parents.values(), [])))

        result = rpa_distinguish(
            curve25519, multipliers, simulated_oracle, bound=isqrt(curve25519.order)
        )
        assert real_mult in result
        # These multipliers are not distinguishable by a binary RPA oracle.
        # assert 1 == len(result)
