from public import public
from typing import MutableMapping

from ...ec.formula import FormulaAction, DoublingFormula, AdditionFormula, TriplingFormula, NegationFormula, \
    DifferentialAdditionFormula, LadderFormula
from ...ec.mult import ScalarMultiplicationAction
from ...ec.point import Point
from ...ec.context import Context, Action


@public
class MultipleContext(Context):
    """A context that traces the multiples computed."""
    base: Point
    points: MutableMapping[Point, int]
    inside: bool

    def enter_action(self, action: Action) -> None:
        if isinstance(action, ScalarMultiplicationAction):
            self.base = action.point
            self.points = {self.base: 1}
            self.inside = True

    def exit_action(self, action: Action) -> None:
        if isinstance(action, ScalarMultiplicationAction):
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
                self.points[dbl] = 2 * self.points[one]
                self.points[add] = self.points[one] + self.points[other]
