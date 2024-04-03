import pytest

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier, AccumulationOrder
from pyecsca.ec.point import Point
from pyecsca.sca.re.zvp import (
    map_to_affine,
    subs_curve_equation,
    remove_z,
    eliminate_y,
    subs_dlog,
    subs_curve_params,
    zvp_points,
    compute_factor_set,
    addition_chain,
    solve_easy_dcp,
    solve_hard_dcp,
)
from pyecsca.ec.formula.unroll import unroll_formula
from pyecsca.ec.context import local, DefaultContext
from sympy import symbols, Poly, sympify, FF


@pytest.fixture(params=["add-2007-bl", "add-2015-rcb", "dbl-2007-bl"])
def formula(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


def test_unroll(formula):
    results = unroll_formula(formula)
    assert results is not None
    for name, res in results:
        assert isinstance(res, Poly)


def test_map_to_affine(formula):
    results = unroll_formula(formula)
    mapped = map_to_affine(formula, results)
    assert mapped is not None
    for name, res in mapped:
        assert isinstance(res, Poly)


def test_factor_set(formula):
    factor_set = compute_factor_set(formula, affine=True)
    assert factor_set is not None
    assert isinstance(factor_set, set)
    expr_set = set(map(lambda poly: poly.as_expr(), factor_set))

    expected_factors = {
        "add-2007-bl": {
            # "y2", RPA
            # "y1", RPA
            # "y1 + y2", RPA
            # "x2", RPA
            # "x1", RPA
            "x1 + x2",
            # "y1^2 + 2*y1*y2 + y2^2 + x1 + x2", Non-homogenous
            # "y1^2 + 2*y1*y2 + y2^2 + 2*x1 + 2*x2", Non-homogenous
            "x1^2 + x1*x2 + x2^2",
            "a + x1^2 + x1*x2 + x2^2",
            # "a^2 + x1^4 + 2*x1^3*x2 + 3*x1^2*x2^2 + 2*x1*x2^3 + x2^4 - x1*y1^2 - x2*y1^2 - 2*x1*y1*y2 - 2*x2*y1*y2 - x1*y2^2 - x2*y2^2 + 2*x1^2*a + 2*x1*x2*a + 2*x2^2*a", RPA
            "2*a^2 + 2*x1^4 + 4*x1^3*x2 + 6*x1^2*x2^2 + 4*x1*x2^3 + 2*x2^4 - 3*x1*y1^2 - 3*x2*y1^2 - 6*x1*y1*y2 - 6*x2*y1*y2 - 3*x1*y2^2 - 3*x2*y2^2 + 4*x1^2*a + 4*x1*x2*a + 4*x2^2*a",
            # "2*a^3 + 2*x1^6 + 6*x1^5*x2 + 12*x1^4*x2^2 + 14*x1^3*x2^3 + 12*x1^2*x2^4 + 6*x1*x2^5 + 2*x2^6 - 3*x1^3*y1^2 - 6*x1^2*x2*y1^2 - 6*x1*x2^2*y1^2 - 3*x2^3*y1^2 - 6*x1^3*y1*y2 - 12*x1^2*x2*y1*y2 - 12*x1*x2^2*y1*y2 - 6*x2^3*y1*y2 - 3*x1^3*y2^2 - 6*x1^2*x2*y2^2 - 6*x1*x2^2*y2^2 - 3*x2^3*y2^2 + 6*x1^4*a + 12*x1^3*x2*a + 18*x1^2*x2^2*a + 12*x1*x2^3*a + 6*x2^4*a + y1^4 + 4*y1^3*y2 + 6*y1^2*y2^2 + 4*y1*y2^3 + y2^4 - 3*x1*y1^2*a - 3*x2*y1^2*a - 6*x1*y1*y2*a - 6*x2*y1*y2*a - 3*x1*y2^2*a - 3*x2*y2^2*a + 6*x1^2*a^2 + 6*x1*x2*a^2 + 6*x2^2*a^2" RPA
        },
        "add-2015-rcb": {
            # "y2", RPA
            "y2 + 1",
            # "y1", RPA
            "y1 + 1",
            "y1 + y2",
            # "x2", RPA
            "x2 + 1",
            "x2 + y2",
            # "x1", RPA
            "x1 + 1",
            "x1 + y1",
            "x1 + x2",
            "x1*a + x2*a + 3*b",
            "-y1*y2 + x1*a + x2*a + 3*b",
            "y1*y2 + 1",
            "y1*y2 + x1*a + x2*a + 3*b",
            "x2*y1 + x1*y2",
            "-x1*x2 + a",
            "x1*x2 + 1",
            "x1*x2 + y1*y2",
            "3*x1*x2 + a",
            "a^2 - x1*x2*a - 3*x1*b - 3*x2*b",
            # "x2*y1^2*y2 + x1*y1*y2^2 - 2*x1*x2*y1*a - x2^2*y1*a - x1^2*y2*a - 2*x1*x2*y2*a + y1*a^2 + y2*a^2 - 3*x1*y1*b - 6*x2*y1*b - 6*x1*y2*b - 3*x2*y2*b", RPA
            # "3*x1*x2^2*y1 + 3*x1^2*x2*y2 + y1^2*y2 + y1*y2^2 + x1*y1*a + 2*x2*y1*a + 2*x1*y2*a + x2*y2*a + 3*y1*b + 3*y2*b", RPA
            # "-3*x1^2*x2^2*a - y1^2*y2^2 + x1^2*a^2 + 4*x1*x2*a^2 + x2^2*a^2 - 9*x1^2*x2*b - 9*x1*x2^2*b + a^3 + 3*x1*a*b + 3*x2*a*b + 9*b^2" RPA
        },
        "dbl-2007-bl": {"a + 3*x1^2", "a^2 + 6*x1^2*a + 9*x1^4 - 12*x1*y1^2"},
    }
    if formula.name in expected_factors:
        expected_set = set(
            map(lambda s: Poly(s).as_expr(), expected_factors[formula.name])
        )
        assert expr_set == expected_set


def test_curve_elimination(secp128r1, formula):
    unrolled = unroll_formula(formula)
    unrolled = map_to_affine(formula, unrolled)
    subbed = subs_curve_equation(unrolled[-1][1], secp128r1.curve)
    assert subbed is not None
    Y1, Y2 = symbols("Y1,Y2")

    # The resulting polynomial should not have Y1 and Y2 in higher powers than 1.
    for term in subbed.terms():
        powers = dict(zip(subbed.gens, term[0]))
        assert powers.get(Y1, 0) in (0, 1)
        assert powers.get(Y2, 0) in (0, 1)


def test_remove_z(secp128r1, formula):
    unrolled = unroll_formula(formula)
    unrolled = map_to_affine(formula, unrolled)
    removed = remove_z(unrolled[-1][1])
    for gen in removed.gens:
        assert not str(gen).startswith("Z")


def test_eliminate_y(secp128r1, formula):
    unrolled = unroll_formula(formula)
    unrolled = map_to_affine(formula, unrolled)
    subbed = subs_curve_equation(unrolled[-1][1], secp128r1.curve)
    eliminated = eliminate_y(subbed, secp128r1.curve.model)
    assert eliminated is not None
    assert isinstance(eliminated, Poly)
    y1, y2 = symbols("y1,y2")

    assert y1 not in eliminated.gens
    assert y2 not in eliminated.gens

    eliminated_second = eliminate_y(eliminated, secp128r1.curve.model)
    assert eliminated_second == eliminated


def test_full(secp128r1, formula):
    unrolled = unroll_formula(formula)
    unrolled = map_to_affine(formula, unrolled)
    subbed = subs_curve_equation(unrolled[-1][1], secp128r1.curve)
    removed = remove_z(subbed)
    eliminated = eliminate_y(removed, secp128r1.curve.model)
    dlog = subs_dlog(eliminated, 3, secp128r1.curve)
    assert dlog is not None
    assert isinstance(dlog, Poly)
    x1, x2 = symbols("x1,x2")
    assert x2 not in dlog.gens

    final = subs_curve_params(dlog, secp128r1.curve)
    assert final is not None
    assert isinstance(final, Poly)
    assert final.gens == (x1,)


@pytest.mark.slow
def test_zvp(secp128r1, formula):
    unrolled = unroll_formula(formula)
    unrolled = map_to_affine(formula, unrolled)
    # Try all intermediates, zvp_point should return empty set if ZVP points do not exist
    # Try with a few scalars to actually test more resulting ZVP points
    for name, poly in unrolled:
        for k in (2, 3, 5):
            points = zvp_points(poly, secp128r1.curve, k, secp128r1.order)
            if points:
                break
        assert isinstance(points, set)

        # If points are produced, try them all.
        for point in points:
            inputs = [point.to_model(formula.coordinate_model, secp128r1.curve)]
            if formula.num_inputs > 1:
                second_point = secp128r1.curve.affine_multiply(point, k)
                inputs.append(
                    second_point.to_model(formula.coordinate_model, secp128r1.curve)
                )
            with local(DefaultContext()) as ctx:
                formula(secp128r1.curve.prime, *inputs, **secp128r1.curve.parameters)
            action = next(iter(ctx.actions.keys()))
            results = list(map(lambda o: int(o.value), action.op_results))
            assert 0 in results


@pytest.mark.parametrize(
    "poly_str,point,k",
    [
        (
            "y1 + y2",
            (
                54027047743185503031379008986257148598,
                42633567686060343012155773792291852040,
            ),
            4,
        ),
        (
            "x1 + x2",
            (
                285130337309757533508049972949147801522,
                55463852278545391044040942536845640298,
            ),
            3,
        ),
        (
            "x1*x2 + y1*y2",
            (
                155681799415564546404955983367992137717,
                227436010604106449719780498844151836756,
            ),
            5,
        ),
        (
            "y1*y2 - x1*a - x2*a - 3*b",
            (
                169722400242675158455680894146658513260,
                33263376472545436059176357032150610796,
            ),
            4,
        ),
        ("x1", (0, 594107526960909229279178399525926007), 3),
        (
            "x2",
            (
                234937379492809870217296988280059595814,
                101935882302108071650074851009662355573,
            ),
            4,
        ),
    ],
)
def test_points(secp128r1, poly_str, point, k):
    pt = Point(
        AffineCoordinateModel(secp128r1.curve.model),
        x=Mod(point[0], secp128r1.curve.prime),
        y=Mod(point[1], secp128r1.curve.prime),
    )
    poly_expr = sympify(poly_str)
    poly = Poly(poly_expr, domain=FF(secp128r1.curve.prime))
    res = zvp_points(poly, secp128r1.curve, k, secp128r1.order)
    assert pt in res


def test_addition_chain(secp128r1):
    res = addition_chain(
        78699,
        secp128r1,
        LTRMultiplier,
        lambda add, dbl: LTRMultiplier(
            add, dbl, None, False, AccumulationOrder.PeqPR, True, True
        ),
    )
    assert res is not None
    assert len(res) == 25


@pytest.mark.parametrize("k", [7, 25, 31])
def test_big_boy(secp128r1, k):
    poly_expr = sympify("x1*x2 + y1*y2")
    poly = Poly(poly_expr, domain=FF(secp128r1.curve.prime))
    res = zvp_points(poly, secp128r1.curve, k, secp128r1.order)
    assert res is not None


@pytest.mark.parametrize("numero", [5, 1, 0])
def test_small_boy(secp128r1, numero):
    x = symbols("x1")
    poly = Poly(numero, x, domain=FF(secp128r1.curve.prime))
    res = solve_easy_dcp(poly, secp128r1.curve)
    assert res is not None
    if numero == 0:
        assert len(res) >= 1


# secp128r1 has a = -3 so the first poly is zero as well
@pytest.mark.parametrize("poly_expr", ["a+3", "0"])
def test_zero_boy(secp128r1, poly_expr):
    x, a = symbols("x1 a")
    poly = Poly(sympify(poly_expr), x, a, domain=FF(secp128r1.curve.prime))
    res = solve_hard_dcp(poly, secp128r1.curve, 5)
    assert res is not None
    assert len(res) >= 1
