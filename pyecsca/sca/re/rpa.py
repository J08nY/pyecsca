"""
Provides functionality inspired by the Refined-Power Analysis attack by Goubin.

  A Refined Power-Analysis Attack on Elliptic Curve Cryptosystems, Louis Goubin, PKC '03
  `<https://dl.acm.org/doi/10.5555/648120.747060>`_
"""
from public import public
from typing import MutableMapping, Optional

from sympy import FF, sympify, Poly, symbols

from ...ec.coordinates import AffineCoordinateModel
from ...ec.formula import (
    FormulaAction,
    DoublingFormula,
    AdditionFormula,
    TriplingFormula,
    NegationFormula,
    DifferentialAdditionFormula,
    LadderFormula,
)
from ...ec.mod import Mod
from ...ec.mult import ScalarMultiplicationAction, PrecomputationAction
from ...ec.params import DomainParameters
from ...ec.model import ShortWeierstrassModel, MontgomeryModel
from ...ec.point import Point
from ...ec.context import Context, Action


@public
class MultipleContext(Context):
    """Context that traces the multiples of points computed."""

    base: Optional[Point]
    points: MutableMapping[Point, int]
    inside: bool

    def __init__(self):
        self.base = None
        self.points = {}
        self.inside = False

    def enter_action(self, action: Action) -> None:
        if isinstance(action, (ScalarMultiplicationAction, PrecomputationAction)):
            if self.base:
                # If we already did some computation with this context try to see if we are building on top of it.
                if self.base != action.point:
                    # If we are not building on top of it we have to forget stuff and set a new base and mapping.
                    self.base = action.point
                    self.points = {self.base: 1}
            else:
                self.base = action.point
                self.points = {self.base: 1}
            self.inside = True

    def exit_action(self, action: Action) -> None:
        if isinstance(action, (ScalarMultiplicationAction, PrecomputationAction)):
            self.inside = False
        if isinstance(action, FormulaAction) and self.inside:
            if isinstance(action.formula, DoublingFormula):
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = 2 * self.points[inp]
            elif isinstance(action.formula, TriplingFormula):
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = 3 * self.points[inp]
            elif isinstance(action.formula, AdditionFormula):
                one, other = action.input_points
                out = action.output_points[0]
                self.points[out] = self.points[one] + self.points[other]
            elif isinstance(action.formula, NegationFormula):
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = -self.points[inp]
            elif isinstance(action.formula, DifferentialAdditionFormula):
                _, one, other = action.input_points
                out = action.output_points[0]
                self.points[out] = self.points[one] + self.points[other]
            elif isinstance(action.formula, LadderFormula):
                _, one, other = action.input_points
                dbl, add = action.output_points
                self.points[add] = self.points[one] + self.points[other]
                self.points[dbl] = 2 * self.points[one]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r}, multiples={self.points.values()!r})"


def rpa_point_0y(params: DomainParameters):
    """Construct a RPA point (0, y) for given domain parameters."""
    if isinstance(params.curve.model, ShortWeierstrassModel):
        if not params.curve.parameters["b"].is_residue():
            return None
        y = params.curve.parameters["b"].sqrt()
        # TODO: We can take the negative as well.
        return Point(AffineCoordinateModel(params.curve.model), x=Mod(0, params.curve.prime), y=y)
    elif isinstance(params.curve.model, MontgomeryModel):
        return Point(AffineCoordinateModel(params.curve.model), x=Mod(0, params.curve.prime),
                     y=Mod(0, params.curve.prime))
    else:
        raise NotImplementedError


def rpa_point_x0(params: DomainParameters):
    """Construct a RPA point (x, 0) for given domain parameters."""
    if isinstance(params.curve.model, ShortWeierstrassModel):
        if (params.order * params.cofactor) % 2 != 0:
            return None
        k = FF(params.curve.prime)
        expr = sympify("x^3 + a * x + b", evaluate=False)
        expr = expr.subs("a", k(int(params.curve.parameters["a"])))
        expr = expr.subs("b", k(int(params.curve.parameters["b"])))
        poly = Poly(expr, symbols("x"), domain=k)
        roots = poly.ground_roots()
        # TODO: There may be more roots.
        if not roots:
            return None
        x = Mod(int(roots[0]), params.curve.prime)
        return Point(AffineCoordinateModel(params.curve.model), x=x, y=Mod(0, params.curve.prime))
    elif isinstance(params.curve.model, MontgomeryModel):
        return Point(AffineCoordinateModel(params.curve.model), x=Mod(0, params.curve.prime),
                     y=Mod(0, params.curve.prime))
    else:
        raise NotImplementedError
