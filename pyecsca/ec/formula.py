from ast import parse, Expression
from typing import List, Set, Any, ClassVar, MutableMapping
from itertools import product

from pkg_resources import resource_stream
from public import public

from .op import CodeOp


class Formula(object):
    """A formula operating on points."""
    name: str
    coordinate_model: Any
    meta: MutableMapping[str, Any]
    parameters: List[str]
    assumptions: List[Expression]
    code: List[CodeOp]
    shortname: ClassVar[str]
    num_inputs: ClassVar[int]
    num_outputs: ClassVar[int]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name} for {self.coordinate_model})"

    @property
    def input_index(self):
        raise NotImplementedError

    @property
    def output_index(self) -> int:
        """The starting index where this formula stores its outputs."""
        raise NotImplementedError

    @property
    def inputs(self) -> Set[str]:
        raise NotImplementedError

    @property
    def outputs(self) -> Set[str]:
        raise NotImplementedError


class EFDFormula(Formula):

    def __init__(self, path: str, name: str, coordinate_model: Any):
        self.name = name
        self.coordinate_model = coordinate_model
        self.meta = {}
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
                    self.meta["source"] = line[7:]
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                            parse(line[7:].replace("=", "==").replace("^", "**"), mode="eval"))
                line = f.readline().decode("ascii")

    def __read_op3_file(self, path):
        with resource_stream(__name__, path) as f:
            for line in f.readlines():
                code_module = parse(line.decode("ascii").replace("^", "**"), path, mode="exec")
                self.code.append(CodeOp(code_module))

    @property
    def input_index(self):
        return 1

    @property
    def output_index(self):
        return max(self.num_inputs + 1, 3)

    @property
    def inputs(self):
        return set(var + str(i) for var, i in product(self.coordinate_model.variables,
                                                      range(1, 1 + self.num_inputs)))

    @property
    def outputs(self):
        return set(var + str(i) for var, i in product(self.coordinate_model.variables,
                                                      range(self.output_index, self.output_index + self.num_outputs)))

    def __eq__(self, other):
        if not isinstance(other, EFDFormula):
            return False
        return self.name == other.name and self.coordinate_model == other.coordinate_model

    def __hash__(self):
        return hash(self.name) + hash(self.coordinate_model)

@public
class AdditionFormula(Formula):
    shortname = "add"
    num_inputs = 2
    num_outputs = 1


@public
class AdditionEFDFormula(AdditionFormula, EFDFormula):
    pass


@public
class DoublingFormula(Formula):
    shortname = "dbl"
    num_inputs = 1
    num_outputs = 1


@public
class DoublingEFDFormula(DoublingFormula, EFDFormula):
    pass


@public
class TriplingFormula(Formula):
    shortname = "tpl"
    num_inputs = 1
    num_outputs = 1


@public
class TriplingEFDFormula(TriplingFormula, EFDFormula):
    pass


@public
class NegationFormula(Formula):
    shortname = "neg"
    num_inputs = 1
    num_outputs = 1


@public
class NegationEFDFormula(NegationFormula, EFDFormula):
    pass


@public
class ScalingFormula(Formula):
    shortname = "scl"
    num_inputs = 1
    num_outputs = 1


@public
class ScalingEFDFormula(ScalingFormula, EFDFormula):
    pass


@public
class DifferentialAdditionFormula(Formula):
    shortname = "dadd"
    num_inputs = 3
    num_outputs = 1


@public
class DifferentialAdditionEFDFormula(DifferentialAdditionFormula, EFDFormula):
    pass


@public
class LadderFormula(Formula):
    shortname = "ladd"
    num_inputs = 3
    num_outputs = 2


@public
class LadderEFDFormula(LadderFormula, EFDFormula):
    pass
