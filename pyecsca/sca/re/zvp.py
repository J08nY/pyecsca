"""
Provides functionality inspired by the Zero-value point attack.

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_

Implements ZVP point construction from [FFD]_.
"""
from typing import List, Set
from public import public
import contextlib

from sympy import symbols, FF, Poly, Monomial, Symbol, Expr

from ...ec.context import DefaultContext, local
from ...ec.curve import EllipticCurve
from ...ec.divpoly import mult_by_n
from ...ec.formula import Formula
from ...ec.mod import SymbolicMod, Mod
from ...ec.point import Point
from ...misc.cfg import TemporaryConfig


@public
def unroll_formula(formula: Formula, prime: int) -> List[Poly]:
    """
    Unroll a given formula symbolically to obtain symbolic expressions for its intermediate values.

    :param formula: Formula to unroll.
    :param prime: Field to unroll over, necessary for technical reasons.
    :return: List of symbolic intermediate values.
    """
    field = FF(prime)
    inputs = [Point(formula.coordinate_model,
                    **{var: SymbolicMod(symbols(var + str(i)), prime) for var in formula.coordinate_model.variables})
              for i in
              range(1, 1 + formula.num_inputs)]
    params = {var: SymbolicMod(symbols(var), prime) for var in formula.coordinate_model.curve_model.parameter_names}
    with local(DefaultContext()) as ctx, TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = "symbolic"
        formula(prime, *inputs, **params)
    return [Poly(op_result.value.x, *op_result.value.x.free_symbols, domain=field) for op_result in
            ctx.actions.get_by_index([0])[0].op_results]


def curve_equation(x: Symbol, curve: EllipticCurve, symbolic: bool = True) -> Expr:
    """
    Get the "ysquared" curve polynomial in :paramref:`~.x` for the :paramref:`~.curve`,
    either symbolically or with concrete parameter values.

    :param x:
    :param curve:
    :param symbolic:
    :return:
    """
    parameters = {name: symbols(name) if symbolic else curve.parameters[name] for name in curve.model.parameter_names}
    return eval(compile(curve.model.ysquared, "", mode="eval"), {"x": x, **parameters})


def subs_curve_equation(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Substitute in the curve equation "ysquared" for Y repeatedly to
    eliminate all but singular powers of Y.

    :param poly:
    :param curve:
    :return:
    """
    terms = []
    for term in poly.terms():
        sub = 1
        new_term = []
        for power, gen in zip(term[0], poly.gens):
            if str(gen).startswith("Y"):
                X = symbols("X" + str(gen)[1:])
                ysquared = curve_equation(X, curve)
                sub *= ysquared ** (power // 2)
                power %= 2
            new_term.append(power)
        expr = Monomial(new_term, poly.gens).as_expr() * sub * term[1]
        terms.append(expr)
    return Poly(sum(terms), domain=poly.domain)


def subs_curve_params(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Substitute in the concrete curve parameters.

    :param poly:
    :param curve:
    :return:
    """
    for name, value in curve.parameters.items():
        symbol = symbols(name)
        if symbol in poly.gens:
            poly = poly.subs(symbol, value)
    return poly


def subs_dlog(poly: Poly, k: int, curve: EllipticCurve):
    """
    Substitute in the multiplication-by-k-map(X1) in place of X2.

    :param poly:
    :param k:
    :param curve:
    :return:
    """
    X1, X2 = symbols("X1,X2")
    if X2 not in poly.gens or X1 not in poly.gens:
        return poly
    max_degree = poly.degree(X2)
    X2i = poly.gens.index(X2)
    new_gens = set(poly.gens)
    new_gens.remove(X2)

    mx, my = mult_by_n(curve, k)
    u, v = mx[0].subs("x", X1), mx[1].subs("x", X1)

    res = 0
    for term in poly.terms():
        powers = list(term[0])
        u_power = powers[X2i]
        u_factor = u**u_power
        v_power = max_degree - u_power
        v_factor = v**v_power
        powers[X2i] = 0
        monom = Monomial(powers, poly.gens).as_expr() * term[1]
        res += Poly(monom, *new_gens, domain=poly.domain) * u_factor * v_factor
    return Poly(res, domain=poly.domain)


def remove_z(poly: Poly) -> Poly:
    """
    Substitute in 1 for all Zs (because we can do that ;).

    :param poly:
    :return:
    """
    for gen in poly.gens:
        if str(gen).startswith("Z"):
            poly = poly.subs(gen, 1)
    return poly


def eliminate_y(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Eliminate the remaining Ys (only power 1).

    See [FFD]_ page 11.

    :param poly:
    :param curve:
    :return:
    """
    Y1, Y2 = symbols("Y1,Y2")
    Y1i = None
    with contextlib.suppress(ValueError):
        Y1i = poly.gens.index(Y1)
    Y2i = None
    with contextlib.suppress(ValueError):
        Y2i = poly.gens.index(Y2)
    f0 = 0
    f1 = 0
    f2 = 0
    f12 = 0
    for term in poly.terms():
        monom = term[0]
        monom_expr = Monomial(term[0], poly.gens).as_expr() * term[1]
        y1_present = not (Y1i is None or monom[Y1i] == 0)
        y2_present = not (Y2i is None or monom[Y2i] == 0)
        if y1_present and y2_present:
            f12 += monom_expr.subs(Y1, 1).subs(Y2, 1)
        elif y1_present and not y2_present:
            f1 += monom_expr.subs(Y1, 1)
        elif not y1_present and y2_present:
            f2 += monom_expr.subs(Y2, 1)
        elif not y1_present and not y2_present:
            f0 += monom_expr
    fe_X1 = curve_equation(symbols("X1"), curve)
    fe_X2 = curve_equation(symbols("X2"), curve)

    # [FFD] page 11
    f_prime = fe_X2 * (fe_X1 * 2 * f1 * f12 - 2 * f0 * f2) ** 2 - \
        (f0 ** 2 + f2 ** 2 * fe_X2 - fe_X1 * (f1 ** 2 + f12 ** 2 * fe_X2)) ** 2
    return Poly(f_prime, domain=poly.domain)


@public
def zvp_point(poly: Poly, curve: EllipticCurve, k: int) -> Set[Point]:
    """
    Find a set of ZVP points for a given intermediate value and dlog relationship.

    :param poly: The polynomial to zero out, obtained as a result of :py:meth:`.unroll_formula`.
    :param curve: The curve to compute over.
    :param k: The discrete-log relationship between the two points, i.e. (X2, Y2) = [k](X1, Y1)
    :return: The set of points (X1, Y1).
    """
    # If input poly is trivial (only in params), abort early
    if not set(symbols("X1,X2,Y1,Y2")).intersection(poly.gens):
        return set()
    # Start with removing all squares of Y1, Y2
    subbed = subs_curve_equation(poly, curve)
    # Remove the Zs by setting them to 1
    removed = remove_z(subbed)
    # Now remove the rest of the Ys by clever curve equation use
    eliminated = eliminate_y(removed, curve)
    # Substitute in the mult-by-k map
    dlog = subs_dlog(eliminated, k, curve)
    # Put in concrete curve parameters
    final = subs_curve_params(dlog, curve)
    # Find the roots (X1)
    roots = final.ground_roots()
    points = set()
    # Finally lift the roots to find the points (if any)
    for root, multiplicity in roots.items():
        pt = curve.affine_lift_x(Mod(int(root), curve.prime))
        # Check that the points zero out the original polynomial to filter out erroneous candidates
        for point in pt:
            other = curve.affine_multiply(point, k)
            inputs = {"X1": point.x, "Y1": point.y, "X2": other.x, "Y2": other.y, "Z1": 1, "Z2": 1, **curve.parameters}
            res = poly.eval([inputs[str(gen)] for gen in poly.gens])
            if res == 0:
                points.add(point)
    return points
