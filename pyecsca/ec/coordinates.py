from ast import parse, Expression
from pkg_resources import resource_listdir, resource_isdir, resource_stream
from typing import List, Any, MutableMapping

from .formula import Formula, AdditionFormula, DoublingFormula, TriplingFormula, DifferentialAdditionFormula, LadderFormula, ScalingFormula

class CoordinateModel(object):
    name: str
    full_name: str
    curve_model: Any
    variables: List[str]
    satisfying: List[Expression]
    parameters: List[str]
    assumptions: List[Expression]
    formulas: MutableMapping[str, Formula]

    def __init__(self, dir_path: str, name: str, curve_model: Any):
        self.name = name
        self.curve_model = curve_model
        self.variables = []
        self.satisfying = []
        self.parameters = []
        self.assumptions = []
        self.formulas = {}
        for fname in resource_listdir(__name__, dir_path):
            file_path = dir_path + "/" + fname
            if resource_isdir(__name__, file_path):
                self.__read_formula_dir(file_path, fname)
            else:
                self.__read_coordinates_file(file_path)

    def __read_formula_dir(self, dir_path, formula_type):
        for fname in resource_listdir(__name__, dir_path):
            if fname.endswith(".op3"):
                continue
            if formula_type == "addition":
                cls = AdditionFormula
            elif formula_type == "doubling":
                cls = DoublingFormula
            elif formula_type == "tripling":
                cls = TriplingFormula
            elif formula_type == "diffadd":
                cls = DifferentialAdditionFormula
            elif formula_type == "ladder":
                cls = LadderFormula
            elif formula_type == "scaling":
                cls = ScalingFormula
            else:
                cls = Formula
            self.formulas[fname] = cls(dir_path + "/" + fname, fname, self)

    def __read_coordinates_file(self, file_path):
        with resource_stream(__name__, file_path) as f:
            line = f.readline().decode("ascii")
            while line:
                line = line[:-1]
                if line.startswith("name"):
                    self.full_name = line[5:]
                elif line.startswith("variable"):
                    self.variables.append(line[9:])
                elif line.startswith("satisfying"):
                    self.satisfying.append(parse(line[11:].replace("=", "==").replace("^", "**"), mode="eval"))
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                        parse(line[7:].replace("=", "==").replace("^", "**"), mode="eval"))
                line = f.readline().decode("ascii")

    def __repr__(self):
        return "CoordinateModel(\"{}\" on {})".format(self.name, self.curve_model.name)
