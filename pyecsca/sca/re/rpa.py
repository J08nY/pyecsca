"""
Provides functionality inspired by the Refined-Power Analysis attack by Goubin.

  A Refined Power-Analysis Attack on Elliptic Curve Cryptosystems, Louis Goubin, PKC '03
  `<https://dl.acm.org/doi/10.5555/648120.747060>`_
"""
from public import public
from typing import MutableMapping, Optional, Callable, List
from collections import Counter

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
from ...ec.mult import ScalarMultiplicationAction, PrecomputationAction, ScalarMultiplier
from ...ec.params import DomainParameters
from ...ec.model import ShortWeierstrassModel, MontgomeryModel
from ...ec.point import Point
from ...ec.context import Context, Action, local


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


def rpa_point_0y(params: DomainParameters) -> Optional[Point]:
    """Construct an (affine) RPA point (0, y) for given domain parameters."""
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


def rpa_point_x0(params: DomainParameters) -> Optional[Point]:
    """Construct an (affine) RPA point (x, 0) for given domain parameters."""
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
        x = Mod(int(next(iter(roots.keys()))), params.curve.prime)
        return Point(AffineCoordinateModel(params.curve.model), x=x, y=Mod(0, params.curve.prime))
    elif isinstance(params.curve.model, MontgomeryModel):
        return Point(AffineCoordinateModel(params.curve.model), x=Mod(0, params.curve.prime),
                     y=Mod(0, params.curve.prime))
    else:
        raise NotImplementedError


def rpa_distinguish(params: DomainParameters, mults: List[ScalarMultiplier], oracle: Callable[[int, Point], bool]) -> List[ScalarMultiplier]:
    """
    Distinguish the scalar multiplier used (from the possible :paramref:`~.rpa_distinguish.mults`) using
    an RPA :paramref:`~.rpa_distinguish.oracle`.

    :param params: The domain parameters to use.
    :param mults: The list of possible multipliers.
    :param oracle: An oracle that returns `True` when an RPA point is encountered during scalar multiplication of the input by the scalar.
    :returns: The list of possible multipliers after distinguishing (ideally just one).
    """
    P0 = rpa_point_0y(params) or rpa_point_x0(params)
    if not P0:
        raise ValueError("There are no RPA-points on the provided curve.")
    print(f"Got RPA point {P0}")
    while True:
        scalar = int(Mod.random(params.order))
        print(f"Got scalar {scalar}")
        print([mult.__class__.__name__ for mult in mults])
        mults_to_multiples = {}
        counts: Counter = Counter()
        for mult in mults:
            with local(MultipleContext()) as ctx:
                mult.init(params, params.generator)
                mult.multiply(scalar)
            multiples = set(ctx.points.values())
            mults_to_multiples[mult] = multiples
            counts.update(multiples)

        # TODO: This lower part can be repeated a few times for the same scalar above, which could reuse
        #       the computed multiples. Can be done until there is some distinguishing multiple.
        #       However, the counts variable needs to be recomputed for the new subset of multipliers.
        nhalf = len(mults) / 2
        best_distinguishing_multiple = None
        best_count = None
        best_nhalf_distance = None
        for multiple, count in counts.items():
            if best_distinguishing_multiple is None or abs(count - nhalf) < best_nhalf_distance:
                best_distinguishing_multiple = multiple
                best_count = count
                best_nhalf_distance = abs(count - nhalf)
        print(f"Chosen best distinguishing multiple {best_distinguishing_multiple} count={best_count} n={len(mults)}")
        if best_count in (0, len(mults)):
            continue

        multiple_inverse = Mod(best_distinguishing_multiple, params.order).inverse()
        P0_inverse = params.curve.affine_multiply(P0, int(multiple_inverse))
        response = oracle(scalar, P0_inverse)
        print(f"Oracle response -> {response}")
        for mult in mults:
            print(mult.__class__.__name__, best_distinguishing_multiple in mults_to_multiples[mult])
        filt = (lambda mult: best_distinguishing_multiple in mults_to_multiples[mult]) if response else (lambda mult: best_distinguishing_multiple not in mults_to_multiples[mult])
        mults = list(filter(filt, mults))
        print([mult.__class__.__name__ for mult in mults])
        print()

        if len(mults) == 1:
            return mults
