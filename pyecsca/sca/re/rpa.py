from public import public
from typing import MutableMapping, Optional

from ...ec.formula import FormulaAction, DoublingFormula, AdditionFormula, TriplingFormula, NegationFormula, \
    DifferentialAdditionFormula, LadderFormula
from ...ec.mult import ScalarMultiplicationAction, PrecomputationAction
from ...ec.point import Point
from ...ec.context import Context, Action


@public
class MultipleContext(Context):
    """A context that traces the multiples of points computed."""
    base: Optional[Point]
    points: MutableMapping[Point, int]
    inside: bool

    def __init__(self):
        self.base = None
        self.points = {}
        self.inside = False

    def enter_action(self, action: Action) -> None:
        if isinstance(action, (ScalarMultiplicationAction, PrecomputationAction)):
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
                self.points[out] = - self.points[inp]
            elif isinstance(action.formula, DifferentialAdditionFormula):
                diff, one, other = action.input_points
                out = action.output_points[0]
                self.points[out] = self.points[one] + self.points[other]
            elif isinstance(action.formula, LadderFormula):
                diff, one, other = action.input_points
                dbl, add = action.output_points
                self.points[add] = self.points[one] + self.points[other]
                self.points[dbl] = 2 * self.points[one]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r}, multiples={self.points.values()!r})"
