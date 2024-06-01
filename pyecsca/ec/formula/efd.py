"""Provides formulas wrapping the [EFD]_."""
from copy import copy

from public import public

from importlib_resources.abc import Traversable
from typing import Any

from pyecsca.ec.formula.code import CodeFormula
from pyecsca.ec.formula.base import (
    Formula,
    CodeOp,
    AdditionFormula,
    DoublingFormula,
    TriplingFormula,
    NegationFormula,
    ScalingFormula,
    DifferentialAdditionFormula,
    LadderFormula,
)

from pyecsca.misc.utils import pexec, peval


@public
class EFDFormula(Formula):
    """Formula from the [EFD]_."""

    def __new__(cls, *args, **kwargs):
        _, _, name, coordinate_model = args
        if name in coordinate_model.formulas:
            return coordinate_model.formulas[name]
        return object.__new__(cls)

    def __init__(
        self,
        meta_path: Traversable,
        op3_path: Traversable,
        name: str,
        coordinate_model: Any,
    ):
        self.name = name
        self.coordinate_model = coordinate_model
        self.meta = {}
        self.parameters = []
        self.assumptions = []
        self.code = []
        self.unified = False
        self.__read_meta_file(meta_path)
        self.__read_op3_file(op3_path)

    def __read_meta_file(self, path: Traversable):
        with path.open("rb") as f:
            line = f.readline().decode("ascii").rstrip()
            while line:
                if line.startswith("source"):
                    self.meta["source"] = line[7:]
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                        peval(line[7:].replace("=", "==").replace("^", "**"))
                    )
                elif line.startswith("unified"):
                    self.unified = True
                line = f.readline().decode("ascii").rstrip()

    def __read_op3_file(self, path: Traversable):
        with path.open("rb") as f:
            for line in f.readlines():
                code_module = pexec(line.decode("ascii").replace("^", "**"))
                self.code.append(CodeOp(code_module))

    def to_code(self) -> CodeFormula:
        for klass in CodeFormula.__subclasses__():
            if self.shortname == klass.shortname:
                return klass(
                    self.name,
                    copy(self.code),
                    self.coordinate_model,
                    copy(self.parameters),
                    copy(self.assumptions),
                    self.unified,
                )
        raise TypeError(f"CodeFormula not found for {self.__class__}.")

    def __getnewargs__(self):
        return None, None, self.name, self.coordinate_model

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass

    def __eq__(self, other):
        if not isinstance(other, EFDFormula):
            return False
        return (
            self.name == other.name and self.coordinate_model == other.coordinate_model
        )

    def __hash__(self):
        return hash((self.coordinate_model, self.name))


@public
class AdditionEFDFormula(AdditionFormula, EFDFormula):
    pass


@public
class DoublingEFDFormula(DoublingFormula, EFDFormula):
    pass


@public
class TriplingEFDFormula(TriplingFormula, EFDFormula):
    pass


@public
class NegationEFDFormula(NegationFormula, EFDFormula):
    pass


@public
class ScalingEFDFormula(ScalingFormula, EFDFormula):
    pass


@public
class DifferentialAdditionEFDFormula(DifferentialAdditionFormula, EFDFormula):
    pass


@public
class LadderEFDFormula(LadderFormula, EFDFormula):
    pass
