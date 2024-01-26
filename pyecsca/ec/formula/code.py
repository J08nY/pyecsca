"""Provides a concrete class of a formula that has a constructor."""

from .base import (
    Formula,
    AdditionFormula,
    DoublingFormula,
    LadderFormula,
    TriplingFormula,
    NegationFormula,
    ScalingFormula,
    DifferentialAdditionFormula,
)


class CodeFormula(Formula):
    def __init__(self, name, code, coordinate_model, parameters, assumptions):
        self.name = name
        self.coordinate_model = coordinate_model
        self.meta = {}
        self.parameters = parameters
        self.assumptions = assumptions
        self.code = code
        self.unified = False

    def __hash__(self):
        return hash(
            (
                self.name,
                self.coordinate_model,
                tuple(self.code),
                tuple(self.parameters),
                tuple(self.assumptions),
            )
        )

    def __eq__(self, other):
        if not isinstance(other, CodeFormula):
            return False
        return (
            self.name == other.name
            and self.coordinate_model == other.coordinate_model
            and self.code == other.code
        )


class CodeAdditionFormula(AdditionFormula, CodeFormula):
    pass


class CodeDoublingFormula(DoublingFormula, CodeFormula):
    pass


class CodeLadderFormula(LadderFormula, CodeFormula):
    pass


class CodeTriplingFormula(TriplingFormula, CodeFormula):
    pass


class CodeNegationFormula(NegationFormula, CodeFormula):
    pass


class CodeScalingFormula(ScalingFormula, CodeFormula):
    pass


class CodeDifferentialAdditionFormula(DifferentialAdditionFormula, CodeFormula):
    pass
