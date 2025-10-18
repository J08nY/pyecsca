from itertools import product
from copy import copy

import pytest

from pyecsca.ec.countermeasures import (
    GroupScalarRandomization,
    AdditiveSplitting,
    MultiplicativeSplitting,
    EuclideanSplitting,
    BrumleyTuveri,
    PointBlinding,
)
from pyecsca.ec.mod import mod
from pyecsca.ec.mult import *


@pytest.fixture(params=["add-1998-cmo-2", "add-2015-rcb"])
def add(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


@pytest.fixture(params=["dbl-1998-cmo-2", "dbl-2015-rcb"])
def dbl(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


@pytest.fixture()
def mults(secp128r1, add, dbl):
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
        "always": (True, False),
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
        "width": (2, 3, 5),
        "direction": tuple(ProcessingDirection),
        "accumulation_order": tuple(AccumulationOrder),
    }
    bgmws = [
        BGMWMultiplier(
            add, dbl, scl=scale, **dict(zip(bgmw_options.keys(), combination))
        )
        for combination in product(*bgmw_options.values())
    ]
    comb_options = {
        "width": (2, 3, 4, 5),
        "accumulation_order": tuple(AccumulationOrder),
    }
    combs = [
        CombMultiplier(
            add, dbl, scl=scale, **dict(zip(comb_options.keys(), combination))
        )
        for combination in product(*comb_options.values())
    ]

    return (
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


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_group_scalar_rand(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    for mult in mults:
        gsr = GroupScalarRandomization(mult)
        gsr.init(secp128r1, secp128r1.generator)
        masked = gsr.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_additive_splitting(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    for mult in mults:
        asplit = AdditiveSplitting(mult, mult)
        asplit.init(secp128r1, secp128r1.generator)
        masked = asplit.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_multiplicative_splitting(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    for mult in mults:
        msplit = MultiplicativeSplitting(mult, mult)
        msplit.init(secp128r1, secp128r1.generator)
        masked = msplit.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_euclidean_splitting(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    for mult in mults:
        esplit = EuclideanSplitting(mult, mult, mult)
        esplit.init(secp128r1, secp128r1.generator)
        masked = esplit.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_brumley_tuveri(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    for mult in mults:
        bt = BrumleyTuveri(mult)
        bt.init(secp128r1, secp128r1.generator)
        masked = bt.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "num",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
    ],
)
def test_point_blinding(mults, secp128r1, num):
    mult = copy(mults[0])
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(num)

    neg = secp128r1.curve.coordinate_model.formulas["neg"]

    for mult in mults:
        pb = PointBlinding(mult, mult, neg=neg)
        pb.init(secp128r1, secp128r1.generator)
        masked = pb.multiply(num)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "scalar",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
        86728612699079982903603364383639280149,
        60032993417060801067503559426926851620,
    ],
)
@pytest.mark.parametrize(
    "one,two",
    product(
        (
            GroupScalarRandomization,
            AdditiveSplitting,
            MultiplicativeSplitting,
            EuclideanSplitting,
            BrumleyTuveri,
            PointBlinding,
        ),
        repeat=2,
    ),
)
def test_combination(scalar, one, two, secp128r1):
    if one == two:
        pytest.skip("Skip identical combinations.")
    mult = LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas["add-2015-rcb"],
        secp128r1.curve.coordinate_model.formulas["dbl-2015-rcb"],
        scl=secp128r1.curve.coordinate_model.formulas["z"],
    )
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(scalar)

    add = secp128r1.curve.coordinate_model.formulas["add-2015-rcb"]
    neg = secp128r1.curve.coordinate_model.formulas["neg"]

    if one in (AdditiveSplitting, EuclideanSplitting):
        layer_one = one.from_single(mult, add=add)
    elif one == PointBlinding:
        layer_one = one.from_single(mult, neg=neg)
    else:
        layer_one = one.from_single(mult)

    if two in (AdditiveSplitting, EuclideanSplitting):
        kws = {"add": add}
    elif two == PointBlinding:
        kws = {"neg": neg}
    else:
        kws = {}

    for i in range(2**two.nmults):
        bits = format(i, f"0{two.nmults}b")
        args = [layer_one if bit == "1" else mult for bit in bits]
        combo = two(*args, **kws)
        combo.init(secp128r1, secp128r1.generator)
        masked = combo.multiply(scalar)
        assert raw.equals(masked)


@pytest.mark.parametrize(
    "scalar",
    [
        3253857902090173296443513219124437746,
        1234567893141592653589793238464338327,
        86728612699079982903603364383639280149,
        60032993417060801067503559426926851620,
    ],
)
@pytest.mark.parametrize(
    "ctr",
    (
        GroupScalarRandomization,
        AdditiveSplitting,
        EuclideanSplitting,
        MultiplicativeSplitting,
        BrumleyTuveri,
    ),
)
def test_rng(scalar, ctr, secp128r1):
    mult = LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas["add-2015-rcb"],
        secp128r1.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )
    mult.init(secp128r1, secp128r1.generator)
    raw = mult.multiply(scalar)

    def rng(n):
        return mod(123456789, n)

    m = ctr.from_single(mult, rng=rng)
    m.init(secp128r1, secp128r1.generator)
    masked = m.multiply(scalar)
    assert raw.equals(masked)
