"""
Provides functionality inspired by the Zero-value point attack

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_
"""

from sympy import symbols, FF, poly

from pyecsca.ec.context import DefaultContext, local
from pyecsca.ec.formula import Formula
from pyecsca.ec.mod import SymbolicMod
from pyecsca.ec.point import Point
from pyecsca.misc.cfg import TemporaryConfig


def unroll_formula(formula: Formula, prime: int):
    inputs = [Point(formula.coordinate_model,
                    **{var: SymbolicMod(symbols(var + str(i)), prime) for var in formula.coordinate_model.variables})
              for i in
              range(1, 1 + formula.num_inputs)]
    params = {var: SymbolicMod(symbols(var), prime) for var in formula.coordinate_model.curve_model.parameter_names}
    with local(DefaultContext()) as ctx, TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = "symbolic"
        formula(prime, *inputs, **params)
    return [op_result.value for op_result in ctx.actions.get_by_index([0])[0].op_results]
