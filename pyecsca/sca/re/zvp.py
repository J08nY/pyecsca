"""
Provides functionality inspired by the Zero-value point attack.

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_
"""
from typing import List

from sympy import symbols

from ...ec.context import DefaultContext, local
from ...ec.formula import Formula
from ...ec.mod import SymbolicMod
from ...ec.point import Point
from ...misc.cfg import TemporaryConfig


def unroll_formula(formula: Formula, prime: int) -> List[SymbolicMod]:
    """
    Unroll a given formula symbolically to obtain symbolic expressions for its intermediate values.

    :param formula: Formula to unroll.
    :param prime: Field to unroll over, necessary for technical reasons.
    :return: List of symbolic intermediate values.
    """
    inputs = [Point(formula.coordinate_model,
                    **{var: SymbolicMod(symbols(var + str(i)), prime) for var in formula.coordinate_model.variables})
              for i in
              range(1, 1 + formula.num_inputs)]
    params = {var: SymbolicMod(symbols(var), prime) for var in formula.coordinate_model.curve_model.parameter_names}
    with local(DefaultContext()) as ctx, TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = "symbolic"
        formula(prime, *inputs, **params)
    return [op_result.value for op_result in ctx.actions.get_by_index([0])[0].op_results]
