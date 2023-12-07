""""""
from functools import cached_property
from itertools import product

from public import public

from importlib_resources.abc import Traversable
from typing import Any
from .base import (
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
from ast import parse


class EFDFormula(Formula):
    """Formula from the [EFD]_."""

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
                        parse(
                            line[7:].replace("=", "==").replace("^", "**"), mode="eval"
                        )
                    )
                elif line.startswith("unified"):
                    self.unified = True
                line = f.readline().decode("ascii").rstrip()

    def __read_op3_file(self, path: Traversable):
        with path.open("rb") as f:
            for line in f.readlines():
                code_module = parse(
                    line.decode("ascii").replace("^", "**"), str(path), mode="exec"
                )
                self.code.append(CodeOp(code_module))

    def __str__(self):
        return f"{self.coordinate_model!s}/{self.name}"

    @cached_property
    def input_index(self):
        return 1

    @cached_property
    def output_index(self):
        return max(self.num_inputs + 1, 3)

    @cached_property
    def inputs(self):
        return {
            var + str(i)
            for var, i in product(
                self.coordinate_model.variables, range(1, 1 + self.num_inputs)
            )
        }

    @cached_property
    def outputs(self):
        return {
            var + str(i)
            for var, i in product(
                self.coordinate_model.variables,
                range(self.output_index, self.output_index + self.num_outputs),
            )
        }

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
