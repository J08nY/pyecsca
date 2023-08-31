import pytest

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point
from pyecsca.sca.re.zvp import unroll_formula, subs_curve_equation, remove_z, eliminate_y, subs_dlog, subs_curve_params, \
    zvp_point
from pyecsca.ec.context import local, DefaultContext
from sympy import symbols, Poly, sympify, FF


@pytest.fixture(params=["add-2007-bl", "add-2016-rcb"])
def formula(secp128r1, request):
    return secp128r1.curve.coordinate_model.formulas[request.param]


def test_unroll(secp128r1, formula):
    results = unroll_formula(formula, secp128r1.curve.prime)
    assert results is not None
    for res in results:
        assert isinstance(res, Poly)


def test_curve_elimination(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    subbed = subs_curve_equation(unrolled[-1], secp128r1.curve)
    assert subbed is not None
    Y1, Y2 = symbols("Y1,Y2")

    # The resulting polynomial should not have Y1 and Y2 in higher powers than 1.
    for term in subbed.terms():
        powers = dict(zip(subbed.gens, term[0]))
        assert powers.get(Y1, 0) in (0, 1)
        assert powers.get(Y2, 0) in (0, 1)


def test_remove_z(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    removed = remove_z(unrolled[-1])
    for gen in removed.gens:
        assert not str(gen).startswith("Z")


def test_eliminate_y(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    subbed = subs_curve_equation(unrolled[-1], secp128r1.curve)
    eliminated = eliminate_y(subbed, secp128r1.curve)
    assert eliminated is not None
    assert isinstance(eliminated, Poly)
    Y1, Y2 = symbols("Y1,Y2")

    assert Y1 not in eliminated.gens
    assert Y2 not in eliminated.gens


def test_full(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    subbed = subs_curve_equation(unrolled[-1], secp128r1.curve)
    removed = remove_z(subbed)
    eliminated = eliminate_y(removed, secp128r1.curve)
    dlog = subs_dlog(eliminated, 3, secp128r1.curve)
    assert dlog is not None
    assert isinstance(dlog, Poly)
    X1, X2 = symbols("X1,X2")
    assert X2 not in dlog.gens

    final = subs_curve_params(dlog, secp128r1.curve)
    assert final is not None
    assert isinstance(final, Poly)
    assert final.gens == (X1,)


@pytest.mark.slow
def test_zvp(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    # Try all intermediates, zvp_point should return empty set if ZVP points do not exist
    for poly in unrolled:
        points = zvp_point(poly, secp128r1.curve, 5)
        assert isinstance(points, set)

        # If points are produced, try them all.
        for point in points:
            second_point = secp128r1.curve.affine_multiply(point, 5)
            p = point.to_model(formula.coordinate_model, secp128r1.curve)
            q = second_point.to_model(formula.coordinate_model, secp128r1.curve)
            with local(DefaultContext()) as ctx:
                formula(secp128r1.curve.prime, p, q, **secp128r1.curve.parameters)
            action = next(iter(ctx.actions.keys()))
            results = list(map(lambda o: int(o.value), action.op_results))
            assert 0 in results


@pytest.mark.parametrize("poly_str,point,k", [
    ("Y1 + Y2", (54027047743185503031379008986257148598, 42633567686060343012155773792291852040), 4),
    ("X1 + X2", (285130337309757533508049972949147801522, 55463852278545391044040942536845640298), 3),
    ("X1*X2 + Y1*Y2", (155681799415564546404955983367992137717, 227436010604106449719780498844151836756), 5),
    ("Y1*Y2 - X1*a - X2*a - 3*b", (169722400242675158455680894146658513260, 33263376472545436059176357032150610796), 4)
])
def test_points(secp128r1, poly_str, point, k):
    pt = Point(AffineCoordinateModel(secp128r1.curve.model),
               x=Mod(point[0], secp128r1.curve.prime),
               y=Mod(point[1], secp128r1.curve.prime))
    poly_expr = sympify(poly_str)
    poly = Poly(poly_expr, domain=FF(secp128r1.curve.prime))
    res = zvp_point(poly, secp128r1.curve, k)
    assert pt in res
