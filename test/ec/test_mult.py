
import pytest

from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    LadderMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SimpleLadderMultiplier,
    DifferentialLadderMultiplier,
    CoronMultiplier, FixedWindowLTRMultiplier,
)
from pyecsca.ec.point import InfinityPoint, Point
from .utils import cartesian


def get_formulas(coords, *names):
    return [coords.formulas[name] for name in names if name is not None]


def assert_pt_equality(one: Point, other: Point, scale):
    if scale:
        assert one == other
    else:
        assert one.equals(other)


def do_basic_test(
        mult_class, params, base, add, dbl, scale, neg=None, **kwargs
):
    mult = mult_class(
        *get_formulas(params.curve.coordinate_model, add, dbl, neg, scale),
        **kwargs
    )
    mult.init(params, base)
    res = mult.multiply(314)
    other = mult.multiply(157)
    mult.init(params, other)
    other = mult.multiply(2)
    assert_pt_equality(res, other, scale)
    mult.init(params, base)
    assert InfinityPoint(params.curve.coordinate_model) == mult.multiply(0)
    return res


@pytest.mark.parametrize("name,add,dbl,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", None),
                         ])
def test_rtl(secp128r1, name, add, dbl, scale):
    do_basic_test(RTLMultiplier, secp128r1, secp128r1.generator, add, dbl, scale)


@pytest.mark.parametrize("name,add,dbl,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", None),
                         ])
def test_ltr(secp128r1, name, add, dbl, scale):
    a = do_basic_test(
        LTRMultiplier, secp128r1, secp128r1.generator, add, dbl, scale
    )
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


@pytest.mark.parametrize("name,add,dbl,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", None),
                         ]
                         )
def test_coron(secp128r1, name, add, dbl, scale):
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


@pytest.mark.parametrize("name,add,dbl,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", None),
                         ])
def test_simple_ladder(secp128r1, name, add, dbl, scale):
    do_basic_test(
        SimpleLadderMultiplier, secp128r1, secp128r1.generator, add, dbl, scale
    )


@pytest.mark.parametrize("name,num,complete",
                         [
                             ("15", 15, True),
                             ("15", 15, False),
                             ("2355498743", 2355498743, True),
                             ("2355498743", 2355498743, False),
                             (
                                     "325385790209017329644351321912443757746",
                                     325385790209017329644351321912443757746,
                                     True,
                             ),
                             (
                                     "325385790209017329644351321912443757746",
                                     325385790209017329644351321912443757746,
                                     False,
                             ),
                         ])
def test_ladder_differential(curve25519, name, num, complete):
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


@pytest.mark.parametrize("name,add,dbl,neg,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", "neg", "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", "neg", None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", "neg", None),
                         ])
def test_binary_naf(secp128r1, name, add, dbl, neg, scale):
    do_basic_test(
        BinaryNAFMultiplier, secp128r1, secp128r1.generator, add, dbl, scale, neg
    )


@pytest.mark.parametrize("name,add,dbl,neg,width,scale",
                         [
                             ("scaled3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, "z"),
                             ("none3", "add-1998-cmo", "dbl-1998-cmo", "neg", 3, None),
                             ("complete3", "add-2016-rcb", "dbl-2016-rcb", "neg", 3, None),
                             ("scaled5", "add-1998-cmo", "dbl-1998-cmo", "neg", 5, "z"),
                             ("none5", "add-1998-cmo", "dbl-1998-cmo", "neg", 5, None),
                             ("complete5", "add-2016-rcb", "dbl-2016-rcb", "neg", 5, None),
                         ])
def test_window_naf(secp128r1, name, add, dbl, neg, width, scale):
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


@pytest.mark.parametrize("name,add,dbl,width,scale",
                         [
                             ("scaled", "add-1998-cmo", "dbl-1998-cmo", 5, "z"),
                             ("complete", "add-2016-rcb", "dbl-2016-rcb", 5, None),
                             ("none", "add-1998-cmo", "dbl-1998-cmo", 5, None),
                         ])
def test_fixed_window(secp128r1, name, add, dbl, width, scale):
    formulas = get_formulas(secp128r1.curve.coordinate_model, add, dbl, scale)
    mult = FixedWindowLTRMultiplier(*formulas[:2], width)
    mult.init(secp128r1, secp128r1.generator)
    res = mult.multiply(157 * 789)
    print(res)


@pytest.mark.parametrize("name,num,add,dbl",
                         cartesian(
                             [
                                 ("10", 10),
                                 ("2355498743", 2355498743),
                                 (
                                         "325385790209017329644351321912443757746",
                                         325385790209017329644351321912443757746,
                                 ),
                             ],
                             [("add-1998-cmo", "dbl-1998-cmo"), ("add-2016-rcb", "dbl-2016-rcb")],
                         )
                         )
def test_basic_multipliers(secp128r1, name, num, add, dbl):
    ltr = LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        ltr.multiply(1)
    ltr.init(secp128r1, secp128r1.generator)
    res_ltr = ltr.multiply(num)
    rtl = RTLMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas["dbl-1998-cmo"],
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        rtl.multiply(1)
    rtl.init(secp128r1, secp128r1.generator)
    res_rtl = rtl.multiply(num)
    assert res_ltr == res_rtl

    ltr_always = LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["z"],
        always=True,
    )
    rtl_always = RTLMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["z"],
        always=True,
    )
    ltr_always.init(secp128r1, secp128r1.generator)
    rtl_always.init(secp128r1, secp128r1.generator)
    res_ltr_always = ltr_always.multiply(num)
    res_rtl_always = rtl_always.multiply(num)
    assert res_ltr == res_ltr_always
    assert res_rtl == res_rtl_always

    bnaf = BinaryNAFMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["neg"],
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        bnaf.multiply(1)
    bnaf.init(secp128r1, secp128r1.generator)
    res_bnaf = bnaf.multiply(num)
    assert res_bnaf == res_ltr

    wnaf = WindowNAFMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["neg"],
        3,
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        wnaf.multiply(1)
    wnaf.init(secp128r1, secp128r1.generator)
    res_wnaf = wnaf.multiply(num)
    assert res_wnaf == res_ltr

    ladder = SimpleLadderMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        ladder.multiply(1)
    ladder.init(secp128r1, secp128r1.generator)
    res_ladder = ladder.multiply(num)
    assert res_ladder == res_ltr

    coron = CoronMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        coron.multiply(1)
    coron.init(secp128r1, secp128r1.generator)
    res_coron = coron.multiply(num)
    assert res_coron == res_ltr

    fixed = FixedWindowLTRMultiplier(
        secp128r1.curve.coordinate_model.formulas[add],
        secp128r1.curve.coordinate_model.formulas[dbl],
        8,
        secp128r1.curve.coordinate_model.formulas["z"],
    )
    with pytest.raises(ValueError):
        fixed.multiply(1)
    fixed.init(secp128r1, secp128r1.generator)
    res_fixed = fixed.multiply(num)
    assert res_fixed == res_ltr


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
