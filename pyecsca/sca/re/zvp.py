"""
Provides functionality inspired by the Zero-value point attack.

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_

Implements ZVP point construction from [FFD]_.
"""
from typing import List, Set, Tuple, Dict
from public import public
from astunparse import unparse

from sympy import FF, Poly, Monomial, Symbol, Expr, sympify, symbols, div

from ...ec.curve import EllipticCurve
from ...ec.divpoly import mult_by_n
from ...ec.formula import Formula
from ...ec.mod import Mod
from ...ec.point import Point


@public
def unroll_formula(formula: Formula) -> List[Tuple[str, Poly]]:
    """
    Unroll a given formula symbolically to obtain symbolic expressions for its intermediate values.

    :param formula: Formula to unroll.
    :return: List of symbolic intermediate values, with associated variable names.
    """
    params = {
        var: symbols(var)
        for var in formula.coordinate_model.curve_model.parameter_names
    }
    inputs = {
        f"{var}{i}": symbols(f"{var}{i}")
        for var in formula.coordinate_model.variables
        for i in range(1, formula.num_inputs + 1)
    }
    for assumption_string in formula.assumptions_str:
        lhs, rhs = assumption_string.split(" == ")
        if lhs in formula.parameters:
            # Handle a symbolic assignment to a new parameter.
            expr = sympify(rhs, evaluate=False)
            for curve_param, value in params.items():
                expr = expr.subs(curve_param, value)
            params[lhs] = expr

    locls = {**params, **inputs}
    values: List[Tuple[str, Poly]] = []
    for op in formula.code:
        result: Expr = op(**locls)  # type: ignore
        locls[op.result] = result
        if result.free_symbols:
            gens = list(result.free_symbols)
            gens.sort(key=str)
            poly = Poly(result, *gens)
            values.append((op.result, poly))
        else:
            # TODO: We cannot create a Poly here, because the result does not have free symbols (i.e. it is a constant)
            pass

    return values


@public
def map_to_affine(formula: Formula, polys: List[Tuple[str, Poly]]) -> List[Tuple[str, Poly]]:
    """
    Map unrolled polynomials of a formula to affine form, using some assumptions along the way (e.g. `Z = 1`).

    :param formula: The formula the polynomials belong to.
    :param polys: The polynomials (intermediate values) to map.
    :return: The mapped intermediate values, with associated variable names.
    """
    # tosystem_map is the mapping of system variables (without indices) in affine variables (without indices)
    tosystem_map = {}
    for code in formula.coordinate_model.tosystem:
        un = unparse(code).strip()
        lhs, rhs = un.split(" = ")
        tosystem_map[lhs] = sympify(rhs, evaluate=False)
    subs_map = {}
    # subs_map specializes the tosystem_map by adding appropriate indices
    for i in range(1, formula.num_inputs + 1):
        for lhs, rhs in tosystem_map.items():
            subs_lhs = lhs + str(i)
            subs_rhs = rhs.subs("x", f"x{i}").subs("y", f"y{i}")
            subs_map[subs_lhs] = subs_rhs

    results = []
    for result_var, value in polys:
        expr = value
        for lhs, rhs in subs_map.items():
            expr = expr.subs(lhs, rhs)
        if expr.free_symbols:
            gens = list(expr.free_symbols)
            gens.sort(key=str)
            poly = Poly(expr, *gens)
            results.append((result_var, poly))
        else:
            # TODO: We cannot create a Poly here, because the result does not have free symbols (i.e. it is a constant)
            #       Though here we do not care.
            pass
    return results


def filter_out_nonhomogenous_polynomials(
    formula: Formula, unrolled: List[Tuple[str, Poly]]
) -> List[Tuple[str, Poly]]:
    """
    Remove unrolled polynomials from unrolled formula that are not homogenous.

    :param formula: The original formula.
    :param unrolled: The unrolled formula to filter.
    :return: The filtered unrolled formula.
    """
    if "mmadd" in formula.name:
        return unrolled
    homogenity_weights = formula.coordinate_model.homogweights

    # we have to group variables by points and check homogenity for each group
    input_variables_grouped: Dict[int, List[str]] = {}
    for var in formula.inputs:
        # here we assume that the index of the variable is <10 and on the last position
        group = input_variables_grouped.setdefault(int(var[-1]), [])
        group.append(var)

    # zadd formulas have Z1=Z2 and so we put all variables in the same group
    if "zadd" in formula.name:
        input_variables_grouped = {1: sum(input_variables_grouped.values(), [])}

    filtered_unroll = []
    for name, polynomial in unrolled:
        homogenous = True
        for point_index, variables in input_variables_grouped.items():
            weighted_variables = [
                (var, homogenity_weights[var[:-1]]) for var in variables
            ]

            # we dont check homogenity for the second point in madd formulas (which is affine)
            if "madd" in formula.name and point_index == 2:
                continue
            homogenous &= is_homogeneous(Poly(polynomial), weighted_variables)
        if homogenous:
            filtered_unroll.append((name, polynomial))
    return filtered_unroll


def is_homogeneous(polynomial: Poly, weighted_variables: List[Tuple[str, int]]) -> bool:
    """
    Determines whether the polynomial is homogenous with respect to the variables and their weights.

    :param polynomial: The polynomial.
    :param weighted_variables: The variables and their weights.
    :return: True if the polynomial is homogenous, otherwise False.
    """
    hom = symbols("hom")
    new_gens = polynomial.gens + (hom,)  # type: ignore[attr-defined]
    univariate_poly = polynomial.subs(
        {var: hom**weight for var, weight in weighted_variables}
    )
    univariate_poly = Poly(univariate_poly, *new_gens, domain=polynomial.domain)
    hom_index = univariate_poly.gens.index(hom)
    degrees = set(monom[hom_index] for monom in univariate_poly.monoms())
    return len(degrees) <= 1


@public
def compute_factor_set(formula: Formula) -> Set[Poly]:
    """
    Compute a set of factors present in the :paramref:`~.compute_factor_set.formula`.

    :param formula: Formula to compute the factor set of.
    :return: The set of factors present in the formula.
    """
    unrolled = unroll_formula(formula)
    unrolled = filter_out_nonhomogenous_polynomials(formula, unrolled)
    unrolled = map_to_affine(formula, unrolled)

    factors = set()
    # Go over all the unrolled intermediates
    for name, poly in unrolled:
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
            # Make sure the poly has canonical gens order
            canonical = reduced.reorder()
            factors.add(canonical)

    factors = filter_out_rpa_polynomials(factors, formula, unrolled)
    return factors


def filter_out_rpa_polynomials(
    factor_set: Set[Poly], formula: Formula, unrolled: List[Tuple[str, Poly]]
) -> Set[Poly]:
    """
    Remove polynomials from factorset that imply RPA points (on input or output).

    :param factor_set: The factor set to filter.
    :param formula: The formula that the factor set belongs to.
    :param unrolled: The unrolled formula.
    :return: The filtered factor set.
    """

    # Find polynomials that define the output variables
    # We save the latest occurrence of output variable in the list of ops
    output_polynomials = {}
    for name, polynomial in unrolled:
        if name in formula.outputs:
            output_polynomials[name] = polynomial

    filtered_factorset = set()
    for poly in factor_set:
        # ignore poly = constant*input_variable
        if poly.is_monomial and poly.is_linear:
            continue
        divisible = False
        for _, output_poly in output_polynomials.items():
            if div(output_poly, poly)[1] == 0:
                divisible = True
        if not divisible:
            filtered_factorset.add(poly)
    return filtered_factorset


def curve_equation(x: Symbol, curve: EllipticCurve, symbolic: bool = True) -> Expr:
    """
    Get the "ysquared" curve polynomial in :paramref:`~.x` for the :paramref:`~.curve`,
    either symbolically or with concrete parameter values.

    :param x: The sympy symbol to use in place of x.
    :param curve: The elliptic curve to use.
    :param symbolic: Whether to get the symbolic equation for the curve (with symbolic parameters) or actual curve parameter values.
    :return: The sympy expression of the "ysquared" curve polynomial.
    """
    parameters = {
        name: symbols(name) if symbolic else curve.parameters[name]
        for name in curve.model.parameter_names
    }
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

    mx, _ = mult_by_n(curve, k, x_only=True)
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
        res += (
            Poly(monom, *new_gens, domain=poly.domain) * uv_factors[(u_power, v_power)]
        )
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
    f_prime = (
        fe_x2 * (fe_x1 * 2 * f1 * f12 - 2 * f0 * f2) ** 2
        - (f0**2 + f2**2 * fe_x2 - fe_x1 * (f1**2 + f12**2 * fe_x2)) ** 2
    )
    return Poly(f_prime, domain=poly.domain)


@public
def zvp_points(poly: Poly, curve: EllipticCurve, k: int, n: int) -> Set[Point]:
    """
    Find a set of (affine) ZVP points for a given intermediate value and dlog relationship.

    :param poly: The polynomial to zero out, obtained as a result of :py:meth:`.unroll_formula` (or its factor).
    :param curve: The curve to compute over.
    :param k: The discrete-log relationship between the two points, i.e. (x2, x2) = [k](x1, x1)
    :param n: The curve order.
    :return: The set of points (x1, x1).
    """
    # If input poly is trivial (only in params), abort early
    if not set(symbols("x1,x2,y1,y2")).intersection(poly.gens):  # type: ignore[attr-defined]
        return set()
    poly = Poly(poly, domain=FF(curve.prime))
    only_1 = all((not str(gen).endswith("2")) for gen in poly.gens)  # type: ignore[attr-defined]
    only_2 = all((not str(gen).endswith("1")) for gen in poly.gens)  # type: ignore[attr-defined]
    # Start with removing all squares of Y1, Y2
    subbed = subs_curve_equation(poly, curve)
    # Remove the Zs by setting them to 1
    removed = remove_z(subbed)
    # Now remove the rest of the Ys by clever curve equation use, the poly is x-only now
    eliminated = eliminate_y(removed, curve)
    points = set()
    # Now decide on the special case:
    if only_1:
        # if only_1, dlog sub is not necessary, also computing the other point is not necessary
        final = subs_curve_params(eliminated, curve)
        roots = final.ground_roots()
        for root, multiplicity in roots.items():
            pt = curve.affine_lift_x(Mod(int(root), curve.prime))
            for point in pt:
                inputs = {"x1": point.x, "y1": point.y, **curve.parameters}
                res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
                if res == 0:
                    points.add(point)
    elif only_2:
        # if only_2, dlog sub is not necessary, then multiply with k_inverse to obtain target point
        final = subs_curve_params(eliminated, curve)
        roots = final.ground_roots()
        k_inv = Mod(k, n).inverse()
        for root, multiplicity in roots.items():
            pt = curve.affine_lift_x(Mod(int(root), curve.prime))
            for point in pt:
                inputs = {"x2": point.x, "y2": point.y, **curve.parameters}
                res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
                if res == 0:
                    one = curve.affine_multiply(point, int(k_inv))
                    points.add(one)
    else:
        # otherwise we need to sub in the dlog and solve the general case
        # Substitute in the mult-by-k map
        dlog = subs_dlog(eliminated, k, curve)
        # Put in concrete curve parameters
        final = subs_curve_params(dlog, curve)
        # Find the roots (X1)
        roots = final.ground_roots()
        # Finally lift the roots to find the points (if any)
        for root, multiplicity in roots.items():
            pt = curve.affine_lift_x(Mod(int(root), curve.prime))
            # Check that the points zero out the original polynomial to filter out erroneous candidates
            for point in pt:
                other = curve.affine_multiply(point, k)
                inputs = {
                    "x1": point.x,
                    "y1": point.y,
                    "x2": other.x,
                    "y2": other.y,
                    **curve.parameters,
                }
                res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
                if res == 0:
                    points.add(point)
    return points
