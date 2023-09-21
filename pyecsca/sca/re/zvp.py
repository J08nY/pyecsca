"""
Provides functionality inspired by the Zero-value point attack.

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_

Implements ZVP point construction from [FFD]_.
"""
from typing import List, Set
from public import public
from astunparse import unparse

from sympy import FF, Poly, Monomial, Symbol, Expr, sympify, symbols

from ...ec.curve import EllipticCurve
from ...ec.divpoly import mult_by_n
from ...ec.formula import Formula
from ...ec.mod import Mod
from ...ec.point import Point


@public
def unroll_formula(formula: Formula, affine: bool = False) -> List[Poly]:
    """
    Unroll a given formula symbolically to obtain symbolic expressions for its intermediate values.

    If :paramref:`~.compute_factor_set.affine` is set, the polynomials are transformed
    to affine form, using some assumptions along the way (e.g. `Z = 1`).

    :param formula: Formula to unroll.
    :param affine: Whether to transform the unrolled polynomials (and thus the resulting factors) into affine form.
    :return: List of symbolic intermediate values, in formula coordinate model.
    """
    params = {var: symbols(var) for var in formula.coordinate_model.curve_model.parameter_names}
    inputs = {f"{var}{i}": symbols(f"{var}{i}") for var in formula.coordinate_model.variables for i in
              range(1, formula.num_inputs + 1)}
    for assumption_string in formula.assumptions_str:
        lhs, rhs = assumption_string.split(" == ")
        if lhs in formula.parameters:
            # Handle a symbolic assignment to a new parameter.
            expr = sympify(rhs, evaluate=False)
            for curve_param, value in params.items():
                expr = expr.subs(curve_param, value)
            params[lhs] = expr
    subs_map = {}
    if affine:
        # tosystem_map is the mapping of system variables (without indices) in affine variables (without indices)
        tosystem_map = {}
        for code in formula.coordinate_model.tosystem:
            un = unparse(code).strip()
            lhs, rhs = un.split(" = ")
            tosystem_map[lhs] = sympify(rhs, evaluate=False)
        # subs_map specializes the tosystem_map by adding appropriate indices
        for i in range(1, formula.num_inputs + 1):
            for lhs, rhs in tosystem_map.items():
                subs_lhs = lhs + str(i)
                subs_rhs = rhs.subs("x", f"x{i}").subs("y", f"y{i}")
                subs_map[subs_lhs] = subs_rhs

    locls = {**params, **inputs}
    values = []
    for op in formula.code:
        result = op(**locls)
        locls[op.result] = result
        values.append(result)

    results = []
    for value in values:
        if affine:
            expr = value
            for lhs, rhs in subs_map.items():
                expr = expr.subs(lhs, rhs)
            if expr.free_symbols:
                gens = list(expr.free_symbols)
                gens.sort(key=str)
                poly = Poly(expr, *gens)
                results.append(poly)
            else:
                # Skip if no variables remain (constant poly)
                continue
        else:
            results.append(Poly(value))
    return results


def compute_factor_set(formula: Formula, affine: bool = False) -> Set[Poly]:
    """
    Compute a set of factors present in the :paramref:`~.compute_factor_set.formula`.

    If :paramref:`~.compute_factor_set.affine` is set, the polynomials are transformed
    to affine form, using some assumptions along the way (e.g. `Z = 1`).

    :param formula: Formula to compute the factor set of.
    :param affine: Whether to transform the unrolled polynomials (and thus the resulting factors) into affine form.
    :return: The set of factors present in the formula.
    """
    unrolled = unroll_formula(formula, affine=affine)
    factors = set()
    # Go over all of the unrolled intermediates
    for poly in unrolled:
        # Factor the intermediate, don't worry about the coeff
        coeff, factor_list = poly.factor_list()
        # Go over all the factors of the intermediate, forget the power
        for factor, power in factor_list:
            # Remove unnecessary variables from the Poly
            reduced = factor.exclude()
            # If there are only one-letter variables remaining, those are only curve parameters
            # so we do not care about the polynomial
            if all(len(str(gen)) == 1 for gen in reduced.gens):  # type: ignore[attr-defined]
                continue
            # Divide out the GCD of the coefficients from the poly
            _, reduced = reduced.primitive()
            factors.add(reduced)
    return factors


def curve_equation(x: Symbol, curve: EllipticCurve, symbolic: bool = True) -> Expr:
    """
    Get the "ysquared" curve polynomial in :paramref:`~.x` for the :paramref:`~.curve`,
    either symbolically or with concrete parameter values.

    :param x: The sympy symbol to use in place of x.
    :param curve: The elliptic curve to use.
    :param symbolic: Whether to get the symbolic equation for the curve (with symbolic parameters) or actual curve parameter values.
    :return: The sympy expression of the "ysquared" curve polynomial.
    """
    parameters = {name: symbols(name) if symbolic else curve.parameters[name] for name in curve.model.parameter_names}
    return eval(compile(curve.model.ysquared, "", mode="eval"), {"x": x, **parameters})


def subs_curve_equation(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Substitute in the curve equation "ysquared" for `y{1,2}` repeatedly to
    eliminate all but singular powers of y.

    :param poly: The sympy polynomial to substitute in.
    :param curve: The elliptic curve to use.
    :return: A polynomial with eliminated all but singular powers of y.
    """
    poly = Poly(poly, domain=FF(curve.prime))
    gens = poly.gens  # type: ignore[attr-defined]
    terms = []
    for term in poly.terms():
        sub = 1
        new_term = []
        for power, gen in zip(term[0], gens):
            if str(gen).startswith("y"):
                x = symbols("x" + str(gen)[1:])
                ysquared = curve_equation(x, curve)
                sub *= ysquared ** (power // 2)
                power %= 2
            new_term.append(power)
        expr = Monomial(new_term, gens).as_expr() * sub * term[1]
        terms.append(expr)
    return Poly(sum(terms), domain=poly.domain)


def subs_curve_params(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Substitute in the concrete curve parameters.

    :param poly: The sympy polynomial to substitute in.
    :param curve: The elliptic curve to use.
    :return: A polynomial with substituted in concrete curve parameters.
    """
    poly = Poly(poly, domain=FF(curve.prime))
    for name, value in curve.parameters.items():
        symbol = symbols(name)
        if symbol in poly.gens:  # type: ignore[attr-defined]
            poly = poly.subs(symbol, value)
    return poly


def subs_dlog(poly: Poly, k: int, curve: EllipticCurve):
    """
    Substitute in the multiplication-by-k-map(x1) in place of x2.

    :param poly: The sympy polynomial to substitute in.
    :param k: The dlog between the points.
    :param curve: The elliptic curve to use.
    :return: A polynomial with the map substituted (with only x1 coords remaining).
    """
    poly = Poly(poly, domain=FF(curve.prime))
    x1, x2 = symbols("x1,x2")
    gens = poly.gens  # type: ignore[attr-defined]
    if x2 not in gens or x1 not in gens:
        return poly
    max_degree = poly.degree(x2)
    x2i = gens.index(x2)
    new_gens = set(gens)
    new_gens.remove(x2)

    mx, my = mult_by_n(curve, k)
    # TODO: my is unnecessary here so maybe add a function to not compute it (speedup).
    u, v = mx[0].subs("x", x1), mx[1].subs("x", x1)

    # The polynomials are quite dense, hence it makes sense
    # to compute all of the u and v powers in advance and
    # just use them, because they will likely all be needed.
    # Note, this has a memory cost...
    u_powers = [1]
    v_powers = [1]
    for i in range(1, max_degree + 1):
        u_powers.append(u_powers[i - 1] * u)
        v_powers.append(v_powers[i - 1] * v)

    uv_factors = {}
    for term in poly.terms():
        u_power = term[0][x2i]
        v_power = max_degree - u_power
        if (u_power, v_power) in uv_factors:
            continue
        uv_factors[(u_power, v_power)] = u_powers[u_power] * v_powers[v_power]

    res = 0
    for term in poly.terms():
        powers = list(term[0])
        u_power = powers[x2i]
        v_power = max_degree - u_power
        powers[x2i] = 0
        monom = Monomial(powers, gens).as_expr() * term[1]
        res += Poly(monom, *new_gens, domain=poly.domain) * uv_factors[(u_power, v_power)]
    return Poly(res, domain=poly.domain)


def remove_z(poly: Poly) -> Poly:
    """
    Substitute in 1 for all Zs (because we can do that ;).

    :param poly: The sympy polynomial to substitute in.
    :return: A polynomial with Zs eliminated.
    """
    for gen in poly.gens:  # type: ignore[attr-defined]
        if str(gen).startswith("Z"):
            poly = poly.subs(gen, 1)
    return poly


def eliminate_y(poly: Poly, curve: EllipticCurve) -> Poly:
    """
    Eliminate the remaining ys (only power 1).

    See [FFD]_ page 11.

    :param poly: The sympy polynomial to eliminate in.
    :param curve: The elliptic curve to use.
    :return:
    """
    poly = Poly(poly, domain=FF(curve.prime))
    x1, x2, y1, y2 = symbols("x1,x2,y1,y2")
    gens = poly.gens  # type: ignore[attr-defined]
    y1i = gens.index(y1) if y1 in gens else None
    y2i = gens.index(y2) if y2 in gens else None
    f0 = 0
    f1 = 0
    f2 = 0
    f12 = 0
    for term in poly.terms():
        monom = term[0]
        monom_expr = Monomial(term[0], gens).as_expr() * term[1]
        y1_present = not (y1i is None or monom[y1i] == 0)
        y2_present = not (y2i is None or monom[y2i] == 0)
        if y1_present and y2_present:
            f12 += monom_expr.subs(y1, 1).subs(y2, 1)
        elif y1_present and not y2_present:
            f1 += monom_expr.subs(y1, 1)
        elif not y1_present and y2_present:
            f2 += monom_expr.subs(y2, 1)
        elif not y1_present and not y2_present:
            f0 += monom_expr
    fe_x1 = curve_equation(x1, curve)
    fe_x2 = curve_equation(x2, curve)

    # [FFD] page 11
    f_prime = fe_x2 * (fe_x1 * 2 * f1 * f12 - 2 * f0 * f2) ** 2 - \
        (f0 ** 2 + f2 ** 2 * fe_x2 - fe_x1 * (f1 ** 2 + f12 ** 2 * fe_x2)) ** 2
    return Poly(f_prime, domain=poly.domain)


@public
def zvp_points(poly: Poly, curve: EllipticCurve, k: int) -> Set[Point]:
    """
    Find a set of (affine) ZVP points for a given intermediate value and dlog relationship.

    :param poly: The polynomial to zero out, obtained as a result of :py:meth:`.unroll_formula` (or its factor).
    :param curve: The curve to compute over.
    :param k: The discrete-log relationship between the two points, i.e. (x2, x2) = [k](x1, x1)
    :return: The set of points (x1, x1).
    """
    # If input poly is trivial (only in params), abort early
    if not set(symbols("x1,x2,y1,y2")).intersection(poly.gens):  # type: ignore[attr-defined]
        return set()
    poly = Poly(poly, domain=FF(curve.prime))
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
            inputs = {"x1": point.x, "y1": point.y, "x2": other.x, "y2": other.y, **curve.parameters}
            res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
            if res == 0:
                points.add(point)
    return points
