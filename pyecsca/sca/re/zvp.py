"""
Provides functionality inspired by the Zero-value point attack [ZVP]_.

Implements ZVP point construction from [FFD]_.
"""
from typing import List, Set, Tuple, Dict, Type
from public import public
from astunparse import unparse

from sympy import FF, Poly, Monomial, Symbol, Expr, sympify, symbols, div
from pyecsca.sca.re.rpa import MultipleContext
from pyecsca.ec.context import local
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.model import CurveModel
from pyecsca.ec.divpoly import mult_by_n
from pyecsca.ec.formula import (
    Formula,
    AdditionFormula,
    DoublingFormula,
    DifferentialAdditionFormula,
    LadderFormula,
    NegationFormula,
)
from pyecsca.ec.formula.fake import FakePoint, FakeFormula
from pyecsca.ec.formula.unroll import unroll_formula
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


has_pari = False
try:
    import cypari2

    has_pari = True
except ImportError:
    cypari2 = None


@public
def map_to_affine(
    formula: Formula, polys: List[Tuple[str, Poly]]
) -> List[Tuple[str, Poly]]:
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
    degrees = {monom[hom_index] for monom in univariate_poly.monoms()}
    return len(degrees) <= 1


@public
def compute_factor_set(
    formula: Formula,
    affine: bool = True,
    filter_nonhomo: bool = True,
    xonly: bool = False,
) -> Set[Poly]:
    """
    Compute a set of factors present in the :paramref:`~.compute_factor_set.formula`.

    :param formula: Formula to compute the factor set of.
    :param affine: Whether to transform the polynomials into affine form.
    :param filter_nonhomo: Whether to filter out non-homogenous polynomials.
    :param xonly: Whether to make the factor set "x"-only by eliminating y-coords using the curve equation.
    :return: The set of factors present in the formula.
    """
    unrolled = unroll_formula(formula)
    if filter_nonhomo:
        unrolled = filter_out_nonhomogenous_polynomials(formula, unrolled)
    if affine:
        unrolled = map_to_affine(formula, unrolled)
    if xonly:
        unrolled = list(
            {
                (name, eliminate_y(poly, formula.coordinate_model.curve_model))
                for name, poly in unrolled
            }
        )

    curve_params = set(formula.coordinate_model.curve_model.parameter_names)

    factors = set()
    # Go over all the unrolled intermediates
    for name, poly in unrolled:
        # Factor the intermediate, don't worry about the coeff
        coeff, factor_list = poly.factor_list()
        # Go over all the factors of the intermediate, forget the power
        for factor, power in factor_list:
            # Remove unnecessary variables from the Poly
            reduced = factor.exclude() if not factor.is_univariate else factor
            # If there are only curve parameters, we do not care about the polynomial
            if set(reduced.gens).issubset(curve_params):  # type: ignore[attr-defined]
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


def symbolic_curve_equation(x: Symbol, model: CurveModel) -> Expr:
    """
    Get the "ysquared" curve polynomial in :paramref:`~.x` for the :paramref:`~.curve`,
    symbolically.

    :param x: The sympy symbol to use in place of x.
    :param model: The curve model to use.
    :return: The sympy expression of the "ysquared" curve polynomial.
    """
    parameters = {name: symbols(name) for name in model.parameter_names}
    return eval(
        compile(model.ysquared, "", mode="eval"), {"x": x, **parameters}
    )  # eval is OK here, skipcq: PYL-W0123


def curve_equation(x: Symbol, curve: EllipticCurve) -> Expr:
    """
    Get the "ysquared" curve polynomial in :paramref:`~.x` for the :paramref:`~.curve`,
    with concrete parameter values.

    :param x: The sympy symbol to use in place of x.
    :param curve: The elliptic curve to use.
    :return: The sympy expression of the "ysquared" curve polynomial.
    """
    return eval(
        compile(curve.model.ysquared, "", mode="eval"), {"x": x, **curve.parameters}
    )  # eval is OK here, skipcq: PYL-W0123


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
                ysquared = symbolic_curve_equation(x, curve.model)
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


def eliminate_y(poly: Poly, model: CurveModel) -> Poly:
    """
    Eliminate the remaining ys (only power 1).

    See [FFD]_ page 11.

    :param poly: The sympy polynomial to eliminate in.
    :param model: The elliptic curve to use.
    :return:
    """
    x1, x2, y1, y2 = symbols("x1,x2,y1,y2")
    gens = poly.gens  # type: ignore[attr-defined]
    y1i = gens.index(y1) if y1 in gens else None
    y2i = gens.index(y2) if y2 in gens else None
    if y1i is None and y2i is None:
        # Already y-only.
        return poly
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
    fe_x1 = symbolic_curve_equation(x1, model)
    fe_x2 = symbolic_curve_equation(x2, model)

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
    :return: The set of points (x1, y1).
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
    eliminated = eliminate_y(removed, curve.model)
    points = set()
    # Now decide on the special case:
    if only_1:
        # if only_1, dlog sub is not necessary, also computing the other point is not necessary
        for point in solve_easy_dcp(eliminated, curve):
            inputs = {"x1": point.x, "y1": point.y, **curve.parameters}
            res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
            if res == 0:
                points.add(point)
    elif only_2:
        # if only_2, dlog sub is not necessary, then multiply with k_inverse to obtain target point
        k_inv = mod(k, n).inverse()
        for point in solve_easy_dcp(eliminated, curve):
            inputs = {"x2": point.x, "y2": point.y, **curve.parameters}
            res = poly.eval([inputs[str(gen)] for gen in poly.gens])  # type: ignore[attr-defined]
            if res == 0:
                one = curve.affine_multiply(point, int(k_inv))
                points.add(one)
    else:
        # otherwise we need to sub in the dlog and solve the general case
        for point in solve_hard_dcp(eliminated, curve, k):
            # Check that the points zero out the original polynomial to filter out erroneous candidates
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


def _deterministic_point_x(curve: EllipticCurve) -> int:
    """Obtain a "random" coordinate `x` on  given curve."""
    x = mod(1, curve.prime)
    while True:
        points = curve.affine_lift_x(x)
        if points:
            return int(x)
        x += 1


def solve_easy_dcp(xonly_polynomial: Poly, curve: EllipticCurve) -> Set[Point]:
    """
    Solve an easy case of the DCP (see [FFD]_) on the `curve` given the `xonly_polynomial`.

    :param xonly_polynomial: The polynomial to zero out.
    :param curve: The curve to work on.
    :return: A set of points that zero out the polynomial.
    """
    points = set()
    final = subs_curve_params(xonly_polynomial, curve)
    # Solve either via pari or if not available sympy.
    if final.is_zero:
        roots = {_deterministic_point_x(curve)}
    elif final.total_degree() == 0:
        roots = set()
    elif has_pari:
        pari = cypari2.Pari()
        polynomial = pari(str(final.expr).replace("**", "^"))
        roots = set(map(int, pari.polrootsmod(polynomial, curve.prime)))
    else:
        roots = final.ground_roots().keys()

    for root in roots:
        points.update(curve.affine_lift_x(mod(int(root), curve.prime)))
    return points


def solve_hard_dcp(xonly_polynomial: Poly, curve: EllipticCurve, k: int) -> Set[Point]:
    """
    Solve a hard case of DCP (see [FFD]_) on the `curve` given the `xonly_polynomial` and the
    dlog relationship between the points `k`.

    :param xonly_polynomial: The polynomial to zero out.
    :param curve: The curve to work on.
    :param k: The relationship between the two points.
    :return: A set of points that zero out the polynomial.
    """
    points = set()
    # Solve either via pari or if not available sympy.
    if has_pari:
        roots = solve_hard_dcp_cypari(xonly_polynomial, curve, k)
    else:
        # Substitute in the mult-by-k map
        dlog = subs_dlog(xonly_polynomial, k, curve)
        # Put in concrete curve parameters
        final = subs_curve_params(dlog, curve)
        if final.is_zero:
            roots = {_deterministic_point_x(curve)}
        else:
            # Find the roots (X1)
            roots = final.ground_roots().keys()

    # Finally lift the roots to find the points (if any)
    for root in roots:
        points.update(curve.affine_lift_x(mod(int(root), curve.prime)))
    return points


def solve_hard_dcp_cypari(
    xonly_polynomial: Poly, curve: EllipticCurve, k: int
) -> Set[int]:
    """Solve hard DCP via pari."""
    try:
        a, b = int(curve.parameters["a"]), int(curve.parameters["b"])
        xonly_polynomial = subs_curve_params(xonly_polynomial, curve)
        if xonly_polynomial.is_zero:
            return {_deterministic_point_x(curve)}

        # k^2 * degree
        # k=25, deg=6, 128bit -> 3765, a 20MB
        # k=32, deg=6, 128bit -> 6150, a 32MB
        # k=10, deg=6, 128bit -> 606, a 4MB
        outdegree = k**2 * xonly_polynomial.total_degree()
        # Magic heuristic, plus some constant term for very small polys
        stacksize = 2 * (outdegree * (40 * curve.prime.bit_length())) + 1000000
        stacksizemax = 15 * stacksize

        pari = cypari2.Pari()
        pari.default("debugmem", 0)  # silence stack warnings
        pari.allocatemem(stacksize, stacksizemax, silent=True)
        e = pari.ellinit([a, b], curve.prime)
        mul = pari.ellxn(e, k)
        x1, x2 = pari("x1"), pari("x2")
        polynomial = pari(str(xonly_polynomial.expr).replace("**", "^"))

        polydeg = pari.poldegree(polynomial, x2)
        subspoly = 0
        x = pari("x")
        num, den = pari.subst(mul[0], x, x1), pari.subst(mul[1], x, x1)
        for deg in range(polydeg + 1):
            monomial = pari.polcoef(polynomial, deg, x2)
            monomial *= num**deg
            monomial *= den ** (polydeg - deg)
            subspoly += monomial
        if subspoly == pari.zero():
            return {_deterministic_point_x(curve)}
        res = set(map(int, pari.polrootsmod(subspoly, curve.prime)))
    except cypari2.PariError as err:
        raise ValueError("PariError " + err.errtext())
    except Exception as err:
        raise ValueError(str(err))
    return res


def addition_chain(
    scalar: int,
    params: DomainParameters,
    mult_class: Type[ScalarMultiplier],
    mult_factory,
) -> List[Tuple[str, Tuple[int, ...]]]:
    """
    Compute the addition chain for a given scalar and multiplier.

    :param scalar: The scalar to compute for.
    :param params: The domain parameters to use.
    :param mult_class: The class of the scalar multiplier to use.
    :param mult_factory: A callable that takes the formulas and instantiates the multiplier.
    :return: A list of tuples, where the first element is the formula shortname (e.g. "add") and the second is a tuple of the dlog
    relationships to the input of the input points to the formula.
    """
    formula_classes: List[Type[Formula]] = list(
        filter(
            lambda klass: klass in mult_class.requires,
            [
                AdditionFormula,
                DifferentialAdditionFormula,
                DoublingFormula,
                LadderFormula,
                NegationFormula,
            ],
        )
    )
    formulas = []
    for formula in formula_classes:
        for subclass in formula.__subclasses__():
            if issubclass(subclass, FakeFormula):
                formulas.append(subclass(params.curve.coordinate_model))
    mult = mult_factory(*formulas)
    mult.init(params, FakePoint(params.curve.coordinate_model))

    with local(MultipleContext()) as mctx:
        mult.multiply(scalar)

    chain = []
    for point, parents in mctx.parents.items():
        if not parents:
            continue
        formula_type = mctx.formulas[point]
        ks = tuple(mctx.points[parent] for parent in parents)
        chain.append((formula_type, ks))
    return chain
