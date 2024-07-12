"""Provides functions for unrolling formula intermediate values symvolically."""

from typing import List, Tuple

from astunparse import unparse
from public import public
from sympy import Expr, symbols, Poly

from pyecsca.misc.cache import sympify
from pyecsca.ec.formula.base import Formula


@public
def unroll_formula_expr(formula: Formula) -> List[Tuple[str, Expr]]:
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
    for coord_assumption in formula.coordinate_model.assumptions:
        assumption_string = unparse(coord_assumption).strip()
        lhs, rhs = assumption_string.split(" = ")
        if lhs in params:
            expr = sympify(rhs, evaluate=False)
            params[lhs] = expr
    for assumption_string in formula.assumptions_str:
        lhs, rhs = assumption_string.split(" == ")
        if lhs in formula.parameters:
            # Handle a symbolic assignment to a new parameter.
            expr = sympify(rhs, evaluate=False)
            for curve_param, value in params.items():
                expr = expr.xreplace({curve_param: value})
            params[lhs] = expr

    locls = {**params, **inputs}
    values: List[Tuple[str, Expr]] = []
    for op in formula.code:
        result: Expr = op(**locls)  # type: ignore
        locls[op.result] = result
        values.append((op.result, result))
    return values


@public
def unroll_formula(formula: Formula) -> List[Tuple[str, Poly]]:
    """
    Unroll a given formula symbolically to obtain symbolic expressions (as Polynomials) for its intermediate values.

    :param formula: Formula to unroll.
    :return: List of symbolic intermediate values, with associated variable names.
    """
    values = unroll_formula_expr(formula)
    polys = []
    for name, result in values:
        if result.free_symbols:
            gens = list(result.free_symbols)
            gens.sort(key=str)
            poly = Poly(result, *gens)
            polys.append((name, poly))
        else:
            # TODO: We cannot create a Poly here, because the result does not have free symbols (i.e. it is a constant)
            pass
    return polys
