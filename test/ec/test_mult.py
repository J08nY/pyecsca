from itertools import product
from typing import Sequence

import pytest

from pyecsca.ec.mult import (
    DoubleAndAddMultiplier,
    LTRMultiplier,
    RTLMultiplier,
    LadderMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SimpleLadderMultiplier,
    DifferentialLadderMultiplier,
    CoronMultiplier,
    FixedWindowLTRMultiplier,
    ProcessingDirection,
    AccumulationOrder,
    ScalarMultiplier,
    SlidingWindowMultiplier,
    BGMWMultiplier,
    CombMultiplier,
    WindowBoothMultiplier,
)
from pyecsca.ec.mult.fixed import FullPrecompMultiplier
from pyecsca.ec.point import InfinityPoint, Point


def get_formulas(coords, *names):
    return [coords.formulas[name] for name in names if name is not None]


def assert_pt_equality(one: Point, other: Point, scale):
    if scale:
        assert one == other
    else:
        assert one.equals(other)


def do_basic_test(mult_class, params, base, add, dbl, scale, neg=None, **kwargs):
    mult = mult_class(
        *get_formulas(params.curve.coordinate_model, add, dbl, neg, scale), **kwargs
    )
    mult.init(params, base)
    res = mult.multiply(314)
    other = mult.multiply(157)
    mult.init(params, other)
    other = mult.multiply(2)
    assert_pt_equality(res, other, scale)
    try:
        affine = params.curve.affine_multiply(base.to_affine(), 314)
        assert_pt_equality(res, affine, False)
    except NotImplementedError:
        pass
    mult.init(params, base)
    assert InfinityPoint(params.curve.coordinate_model) == mult.multiply(0)
    return res


@pytest.mark.parametrize(
    "add,dbl,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", None),
    ],
)
def test_rtl(secp128r1, add, dbl, scale):
    do_basic_test(RTLMultiplier, secp128r1, secp128r1.generator, add, dbl, scale)


@pytest.mark.parametrize(
    "add,dbl,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", None),
    ],
)
def test_ltr(secp128r1, add, dbl, scale):
    a = do_basic_test(LTRMultiplier, secp128r1, secp128r1.generator, add, dbl, scale)
    b = do_basic_test(
        LTRMultiplier, secp128r1, secp128r1.generator, add, dbl, scale, always=True
    )
    c = do_basic_test(
        LTRMultiplier, secp128r1, secp128r1.generator, add, dbl, scale, complete=False
    )
    d = do_basic_test(
        LTRMultiplier,
        secp128r1,
        secp128r1.generator,
        add,
        dbl,
        scale,
        always=True,
        complete=False,
    )
    assert_pt_equality(a, b, scale)
    assert_pt_equality(b, c, scale)
    assert_pt_equality(c, d, scale)


@pytest.mark.parametrize(
    "add,dbl,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", None),
    ],
)
def test_doubleandadd(secp128r1, add, dbl, scale):
    a = do_basic_test(
        DoubleAndAddMultiplier, secp128r1, secp128r1.generator, add, dbl, scale
    )
    b = do_basic_test(
        DoubleAndAddMultiplier,
        secp128r1,
        secp128r1.generator,
        add,
        dbl,
        scale,
        direction=ProcessingDirection.RTL,
    )
    c = do_basic_test(
        DoubleAndAddMultiplier,
        secp128r1,
        secp128r1.generator,
        add,
        dbl,
        scale,
        accumulation_order=AccumulationOrder.PeqPR,
    )
    d = do_basic_test(
        DoubleAndAddMultiplier,
        secp128r1,
        secp128r1.generator,
        add,
        dbl,
        scale,
        always=True,
        complete=False,
    )
    assert_pt_equality(a, b, scale)
    assert_pt_equality(b, c, scale)
    assert_pt_equality(c, d, scale)


@pytest.mark.parametrize(
    "add,dbl,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", None),
    ],
)
def test_coron(secp128r1, add, dbl, scale):
    do_basic_test(CoronMultiplier, secp128r1, secp128r1.generator, add, dbl, scale)


def test_ladder(curve25519):
    a = do_basic_test(
        LadderMultiplier,
        curve25519,
        curve25519.generator,
        "ladd-1987-m",
        "dbl-1987-m",
        "scale",
    )
    b = do_basic_test(
        LadderMultiplier,
        curve25519,
        curve25519.generator,
        "ladd-1987-m",
        "dbl-1987-m",
        "scale",
        complete=False,
    )
    assert_pt_equality(a, b, True)


@pytest.mark.parametrize(
    "add,dbl,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", None),
    ],
)
def test_simple_ladder(secp128r1, add, dbl, scale):
    do_basic_test(
        SimpleLadderMultiplier, secp128r1, secp128r1.generator, add, dbl, scale
    )


@pytest.mark.parametrize(
    "num,complete",
    [
        (15, True),
        (15, False),
        (2355498743, True),
        (2355498743, False),
        (325385790209017329644351321912443757746, True),
        (325385790209017329644351321912443757746, False),
    ],
)
def test_ladder_differential(curve25519, num, complete):
    ladder = LadderMultiplier(
        curve25519.curve.coordinate_model.formulas["ladd-1987-m"],
        curve25519.curve.coordinate_model.formulas["dbl-1987-m"],
        curve25519.curve.coordinate_model.formulas["scale"],
        complete=complete,
    )
    differential = DifferentialLadderMultiplier(
        curve25519.curve.coordinate_model.formulas["dadd-1987-m"],
        curve25519.curve.coordinate_model.formulas["dbl-1987-m"],
        curve25519.curve.coordinate_model.formulas["scale"],
        complete=complete,
    )
    ladder.init(curve25519, curve25519.generator)
    res_ladder = ladder.multiply(num)
    differential.init(curve25519, curve25519.generator)
    res_differential = differential.multiply(num)
    assert res_ladder == res_differential
    assert InfinityPoint(curve25519.curve.coordinate_model) == differential.multiply(0)


@pytest.mark.parametrize(
    "add,dbl,neg,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", "z"),
        ("add-2015-rcb", "dbl-2015-rcb", "neg", None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", None),
    ],
)
def test_binary_naf(secp128r1, add, dbl, neg, scale):
    do_basic_test(
        BinaryNAFMultiplier, secp128r1, secp128r1.generator, add, dbl, scale, neg
    )


@pytest.mark.parametrize(
    "add,dbl,neg,width,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 3, "z"),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 3, None),
        ("add-2015-rcb", "dbl-2015-rcb", "neg", 3, None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 5, "z"),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 5, None),
        ("add-2015-rcb", "dbl-2015-rcb", "neg", 5, None),
    ],
)
def test_window_naf(secp128r1, add, dbl, neg, width, scale):
    formulas = get_formulas(secp128r1.curve.coordinate_model, add, dbl, neg, scale)
    mult = WindowNAFMultiplier(*formulas[:3], width, *formulas[3:])
    mult.init(secp128r1, secp128r1.generator)
    res = mult.multiply(157 * 789)
    other = mult.multiply(157)
    mult.init(secp128r1, other)
    other = mult.multiply(789)
    assert_pt_equality(res, other, scale)
    mult.init(secp128r1, secp128r1.generator)
    assert InfinityPoint(secp128r1.curve.coordinate_model) == mult.multiply(0)

    mult = WindowNAFMultiplier(
        *formulas[:3], width, *formulas[3:], precompute_negation=True
    )
    mult.init(secp128r1, secp128r1.generator)
    res_precompute = mult.multiply(157 * 789)
    assert_pt_equality(res_precompute, res, scale)


@pytest.mark.parametrize(
    "add,dbl,width,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", 5, "z"),
        ("add-2015-rcb", "dbl-2015-rcb", 5, None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", 5, None),
    ],
)
def test_fixed_window(secp128r1, add, dbl, width, scale):
    formulas = get_formulas(secp128r1.curve.coordinate_model, add, dbl, scale)
    mult = FixedWindowLTRMultiplier(*formulas[:2], width, *formulas[2:])
    mult.init(secp128r1, secp128r1.generator)
    res = mult.multiply(157 * 789)
    other = mult.multiply(157)
    mult.init(secp128r1, other)
    other = mult.multiply(789)
    assert_pt_equality(res, other, scale)
    mult.init(secp128r1, secp128r1.generator)
    assert InfinityPoint(secp128r1.curve.coordinate_model) == mult.multiply(0)


@pytest.mark.parametrize(
    "add,dbl,neg,width,scale",
    [
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 5, "z"),
        ("add-2015-rcb", "dbl-2015-rcb", "neg", 5, None),
        ("add-1998-cmo-2", "dbl-1998-cmo-2", "neg", 5, None),
    ],
)
def test_booth_window(secp128r1, add, dbl, neg, width, scale):
    formulas = get_formulas(secp128r1.curve.coordinate_model, add, dbl, neg, scale)
    mult = WindowBoothMultiplier(*formulas[:3], width, *formulas[3:])
    mult.init(secp128r1, secp128r1.generator)
    res = mult.multiply(157 * 789)
    other = mult.multiply(157)
    mult.init(secp128r1, other)
    other = mult.multiply(789)
    assert_pt_equality(res, other, scale)
    mult.init(secp128r1, secp128r1.generator)
    assert InfinityPoint(secp128r1.curve.coordinate_model) == mult.multiply(0)


@pytest.fixture(params=["add-1998-cmo-2", "add-2015-rcb"])
def add(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


@pytest.fixture(params=["dbl-1998-cmo-2", "dbl-2015-rcb"])
def dbl(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


@pytest.mark.parametrize(
    "num", [10, 2355498743, 325385790209017329644351321912443757746]
)
def test_basic_multipliers(secp128r1, num, add, dbl):
    neg = secp128r1.curve.coordinate_model.formulas["neg"]
    scale = secp128r1.curve.coordinate_model.formulas["z"]

    ltr_options = {
        "always": (True, False),
        "complete": (True, False),
        "accumulation_order": tuple(AccumulationOrder),
    }
    ltrs = [
        LTRMultiplier(add, dbl, scale, **dict(zip(ltr_options.keys(), combination)))
        for combination in product(*ltr_options.values())
    ]
    rtl_options = ltr_options
    rtls = [
        RTLMultiplier(add, dbl, scale, **dict(zip(rtl_options.keys(), combination)))
        for combination in product(*rtl_options.values())
    ]
    bnaf_options = {
        "direction": tuple(ProcessingDirection),
        "accumulation_order": tuple(AccumulationOrder),
    }
    bnafs = [
        BinaryNAFMultiplier(
            add, dbl, neg, scale, **dict(zip(bnaf_options.keys(), combination))
        )
        for combination in product(*bnaf_options.values())
    ]
    wnaf_options = {
        "precompute_negation": (True, False),
        "width": (3, 5),
        "accumulation_order": tuple(AccumulationOrder),
    }
    wnafs = [
        WindowNAFMultiplier(
            add, dbl, neg, scl=scale, **dict(zip(wnaf_options.keys(), combination))
        )
        for combination in product(*wnaf_options.values())
    ]
    booth_options = {
        "precompute_negation": (True, False),
        "width": (3, 5),
        "accumulation_order": tuple(AccumulationOrder),
    }
    booths = [
        WindowBoothMultiplier(
            add, dbl, neg, scl=scale, **dict(zip(booth_options.keys(), combination))
        )
        for combination in product(*booth_options.values())
    ]
    ladder_options = {"complete": (True, False)}
    ladders = [
        SimpleLadderMultiplier(
            add, dbl, scale, **dict(zip(ladder_options.keys(), combination))
        )
        for combination in product(*ladder_options.values())
    ]
    fixed_options = {"m": (5, 8), "accumulation_order": tuple(AccumulationOrder)}
    fixeds = [
        FixedWindowLTRMultiplier(
            add, dbl, scl=scale, **dict(zip(fixed_options.keys(), combination))
        )
        for combination in product(*fixed_options.values())
    ]
    sliding_options = {
        "width": (3, 5),
        "recoding_direction": tuple(ProcessingDirection),
        "accumulation_order": tuple(AccumulationOrder),
    }
    slides = [
        SlidingWindowMultiplier(
            add, dbl, scl=scale, **dict(zip(sliding_options.keys(), combination))
        )
        for combination in product(*sliding_options.values())
    ]
    precomp_options = {
        "always": (True, False),
        "complete": (True, False),
        "direction": tuple(ProcessingDirection),
        "accumulation_order": tuple(AccumulationOrder),
    }
    precomps = [
        FullPrecompMultiplier(
            add, dbl, scl=scale, **dict(zip(precomp_options.keys(), combination))
        )
        for combination in product(*precomp_options.values())
    ]
    bgmw_options = {
        "width": (3, 5),
        "direction": tuple(ProcessingDirection),
        "accumulation_order": tuple(AccumulationOrder),
    }
    bgmws = [
        BGMWMultiplier(
            add, dbl, scl=scale, **dict(zip(bgmw_options.keys(), combination))
        )
        for combination in product(*bgmw_options.values())
    ]
    comb_options = {"width": (2, 3, 5), "accumulation_order": tuple(AccumulationOrder)}
    combs = [
        CombMultiplier(
            add, dbl, scl=scale, **dict(zip(comb_options.keys(), combination))
        )
        for combination in product(*comb_options.values())
    ]

    mults: Sequence[ScalarMultiplier] = (
        ltrs
        + rtls
        + bnafs
        + wnafs
        + booths
        + [CoronMultiplier(add, dbl, scale)]
        + ladders
        + fixeds
        + slides
        + precomps
        + bgmws
        + combs
    )
    results = []
    for mult in mults:
        mult.init(secp128r1, secp128r1.generator)
        res = mult.multiply(num)
        if results:
            assert (
                res == results[-1]
            ), f"Points not equal {res} != {results[-1]} for mult = {mult}"
        results.append(res)


def test_init_fail(curve25519, secp128r1):
    mult = DifferentialLadderMultiplier(
        curve25519.curve.coordinate_model.formulas["dadd-1987-m"],
        curve25519.curve.coordinate_model.formulas["dbl-1987-m"],
        curve25519.curve.coordinate_model.formulas["scale"],
    )
    with pytest.raises(ValueError):
        mult.init(secp128r1, secp128r1.generator)

    with pytest.raises(ValueError):
        LadderMultiplier(
            curve25519.curve.coordinate_model.formulas["ladd-1987-m"],
            scl=curve25519.curve.coordinate_model.formulas["scale"],
            complete=False,
        )
