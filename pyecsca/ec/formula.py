from ast import parse, Expression, Module
from pkg_resources import resource_stream
from typing import List, Any


class Formula(object):
    name: str
    coordinate_model: Any
    source: str
    parameters: List[str]
    assumptions: List[Expression]
    code: List[Module]
    _inputs: int
    _outputs: int

    def __init__(self, path: str, name: str, coordinate_model: Any):
        self.name = name
        self.coordinate_model = coordinate_model
        self.parameters = []
        self.assumptions = []
        self.code = []
        self.__read_meta_file(path)
        self.__read_op3_file(path + ".op3")

    def __read_meta_file(self, path):
        with resource_stream(__name__, path) as f:
            line = f.readline().decode("ascii")
            while line:
                line = line[:-1]
                if line.startswith("source"):
                    self.source = line[7:]
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                            parse(line[7:].replace("=", "==").replace("^", "**"), mode="eval"))
                line = f.readline().decode("ascii")

    def __read_op3_file(self, path):
        with resource_stream(__name__, path) as f:
            for line in f.readlines():
                self.code.append(parse(line.decode("ascii").replace("^", "**"), path, mode="exec"))

    @property
    def num_inputs(self):
        return self._inputs

    @property
    def num_outputs(self):
        return self._outputs

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name} for {self.coordinate_model})"


class AdditionFormula(Formula):
    _inputs = 2
    _outputs = 1


class DoublingFormula(Formula):
    _inputs = 1
    _outputs = 1


class TriplingFormula(Formula):
    _inputs = 1
    _outputs = 1


class NegationFormula(Formula):
    _inputs = 1
    _outputs = 1


class ScalingFormula(Formula):
    _inputs = 1
    _outputs = 1


class DifferentialAdditionFormula(Formula):
    _inputs = 3
    _outputs = 1


class LadderFormula(Formula):
    _inputs = 3
    _outputs = 2
