"""Provides a concrete class of a formula that has a constructor."""
from typing import List, Any
from ast import Expression
from astunparse import unparse

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
from ..op import CodeOp
from ...misc.utils import peval


class CodeFormula(Formula):
    """A basic formula class that can be directly initialized with the code and other attributes."""

    def __init__(
        self,
        name: str,
        code: List[CodeOp],
        coordinate_model: Any,
        parameters: List[str],
        assumptions: List[Expression],
        unified: bool = False,
    ):
        self.name = name
        self.code = code
        self.coordinate_model = coordinate_model
        self.meta = {}
        self.parameters = parameters
        self.assumptions = assumptions
        self.unified = unified

    def __hash__(self):
        return hash(
            (
                self.name,
                self.coordinate_model,
                tuple(self.code),
                tuple(self.parameters),
                tuple(self.assumptions_str),
                self.unified,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, CodeFormula):
            return False
        return (
            self.name == other.name
            and self.coordinate_model == other.coordinate_model
            and self.code == other.code
            and self.parameters == other.parameters
            and self.assumptions_str == other.assumptions_str
            and self.unified == other.unified
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        state["assumptions"] = list(map(unparse, state["assumptions"]))
        return state

    def __setstate__(self, state):
        state["assumptions"] = list(map(peval, state["assumptions"]))
        self.__dict__.update(state)


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
