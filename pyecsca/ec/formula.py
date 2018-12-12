from ast import parse, Expression, Module
from pkg_resources import resource_stream
from typing import List, Any


class Formula(object):
    name: str
    coordinate_model: Any
    source: str
    parameters: List[str]
    assumptions: List[Expression]
    code: Module

    def __init__(self, path: str, name: str, coordinate_model: Any):
        self.name = name
        self.coordinate_model = coordinate_model
        self.parameters = []
        self.assumptions = []
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
            self.code = parse(f.read(), path, mode="exec")

    def __repr__(self):
        return self.__class__.__name__ + "({} for {})".format(self.name, self.coordinate_model)


class AdditionFormula(Formula):
    pass


class DoublingFormula(Formula):
    pass


class TriplingFormula(Formula):
    pass


class ScalingFormula(Formula):
    pass


class DifferentialAdditionFormula(Formula):
    pass


class LadderFormula(Formula):
    pass
