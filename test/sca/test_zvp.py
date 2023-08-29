import pytest

from pyecsca.sca.re.zvp import unroll_formula, subs_curve_equation, remove_z, eliminate_y, subs_dlog, subs_curve_params, \
    zvp_point
from pyecsca.ec.context import local, DefaultContext
from pyecsca.ec.formula import FormulaAction
from sympy import symbols, Poly


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


def test_zvp(secp128r1, formula):
    unrolled = unroll_formula(formula, secp128r1.curve.prime)
    poly = unrolled[-2]
    points = zvp_point(poly, secp128r1.curve, 5)
    assert isinstance(points, set)

    for point in points:
        second_point = secp128r1.curve.affine_multiply(point, 5)
        p = point.to_model(formula.coordinate_model, secp128r1.curve)
        q = second_point.to_model(formula.coordinate_model, secp128r1.curve)
        with local(DefaultContext()) as ctx:
            formula(secp128r1.curve.prime, p, q, **secp128r1.curve.parameters)
        action = next(iter(ctx.actions.keys()))
        results = list(map(lambda o: int(o.value), action.op_results))
        assert 0 in results
