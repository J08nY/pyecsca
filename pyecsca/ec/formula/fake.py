"""Provides "fake" formulas."""
from abc import ABC
from typing import Any, Tuple

from public import public

from pyecsca.ec.formula.base import (
    AdditionFormula,
    FormulaAction,
    Formula,
    DoublingFormula,
    TriplingFormula,
    LadderFormula,
    NegationFormula,
    ScalingFormula,
    DifferentialAdditionFormula,
)
from pyecsca.ec.mod import Mod, Undefined
from pyecsca.ec.point import Point


@public
class FakeFormula(Formula, ABC):
    """
    No matter what the input point is, it just returns the right amount of FakePoints.

    Useful for computing with the scalar multipliers without having concrete formulas
    and points (for example to get the addition chain via the MultipleContext).
    """

    def __init__(self, coordinate_model):
        # TODO: This is missing all of the other attributes
        self.coordinate_model = coordinate_model
        self.code = []

    def __call__(self, field: int, *points: Any, **params: Mod) -> Tuple[Any, ...]:
        with FormulaAction(self, *points, **params) as action:
            result = []
            for i in range(self.num_outputs):
                res = FakePoint(self.coordinate_model)
                action.output_points.append(res)
                result.append(res)
            return action.exit(tuple(result))


@public
class FakeAdditionFormula(FakeFormula, AdditionFormula):
    name = "fake"


@public
class FakeDoublingFormula(FakeFormula, DoublingFormula):
    name = "fake"


@public
class FakeTriplingFormula(FakeFormula, TriplingFormula):
    name = "fake"


@public
class FakeNegationFormula(FakeFormula, NegationFormula):
    name = "fake"


@public
class FakeScalingFormula(FakeFormula, ScalingFormula):
    name = "fake"


@public
class FakeDifferentialAdditionFormula(FakeFormula, DifferentialAdditionFormula):
    name = "fake"


@public
class FakeLadderFormula(FakeFormula, LadderFormula):
    name = "fake"


@public
class FakePoint(Point):
    """Just a fake point."""

    def __init__(self, model):
        coords = {key: Undefined() for key in model.variables}
        super().__init__(model, **coords)

    def __str__(self):
        return "FakePoint"

    def __repr__(self):
        return str(self)
