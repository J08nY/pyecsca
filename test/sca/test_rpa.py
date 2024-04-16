import pytest

from pyecsca.ec.context import local
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
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
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import (
    MultipleContext,
    rpa_point_0y,
    rpa_point_x0,
    rpa_distinguish,
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
    a = Mod(0x7FC57B4110698BC0, p)
    b = Mod(0x37113EA591B04527, p)
    gx = Mod(0x80D2D78FDDB97597, p)
    gy = Mod(0x5586D818B7910930, p)
    # (0x4880bcf620852a54, 0) RPA point
    # (0, 0x6bed3155c9ada064) RPA point

    infty = Point(coords, X=Mod(0, p), Y=Mod(1, p), Z=Mod(0, p))
    g = Point(coords, X=gx, Y=gy, Z=Mod(1, p))
    curve = EllipticCurve(model, coords, p, infty, dict(a=a, b=b))
    return DomainParameters(curve, g, 0x85D265932D90785C, 1)


def test_x0_point(rpa_params):
    res = rpa_point_x0(rpa_params)
    assert res is not None
    assert res.y == 0


def test_0y_point(rpa_params):
    res = rpa_point_0y(rpa_params)
    assert res is not None
    assert res.x == 0


def test_distinguish(secp128r1, add, dbl, neg):
    multipliers = [
        LTRMultiplier(add, dbl, None, False, AccumulationOrder.PeqPR, True, True),
        LTRMultiplier(add, dbl, None, True, AccumulationOrder.PeqPR, True, True),
        RTLMultiplier(add, dbl, None, False, AccumulationOrder.PeqPR, True),
        RTLMultiplier(add, dbl, None, True, AccumulationOrder.PeqPR, False),
        SimpleLadderMultiplier(add, dbl, None, True, True),
        BinaryNAFMultiplier(
            add, dbl, neg, None, ProcessingDirection.LTR, AccumulationOrder.PeqPR, True
        ),
        BinaryNAFMultiplier(
            add, dbl, neg, None, ProcessingDirection.RTL, AccumulationOrder.PeqPR, True
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
        CombMultiplier(add, dbl, 2, None, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 3, None, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 4, None, AccumulationOrder.PeqPR, True),
        CombMultiplier(add, dbl, 5, None, AccumulationOrder.PeqPR, True),
    ]
    for real_mult in multipliers:

        def simulated_oracle(scalar, affine_point):
            point = affine_point.to_model(
                secp128r1.curve.coordinate_model, secp128r1.curve
            )
            with local(MultipleContext()) as ctx:
                real_mult.init(secp128r1, point)
                real_mult.multiply(scalar)
            return any(
                map(lambda P: P.X == 0 or P.Y == 0, sum(ctx.parents.values(), []))
            )

        result = rpa_distinguish(secp128r1, multipliers, simulated_oracle)
        assert real_mult in result
        assert 1 == len(result)
