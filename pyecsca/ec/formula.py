from abc import ABC, abstractmethod
from ast import parse, Expression, Mult, Add, Sub, Pow, Div
from itertools import product
from typing import List, Set, Any, ClassVar, MutableMapping, Tuple, Union

from pkg_resources import resource_stream
from public import public

from .context import Action
from .mod import Mod
from .op import CodeOp, OpType


@public
class OpResult(object):
    """A result of an operation."""
    parents: Tuple
    op: OpType
    name: str
    value: Mod

    def __init__(self, name: str, value: Mod, op: OpType, *parents: Any):
        self.parents = tuple(parents)
        self.name = name
        self.value = value
        self.op = op

    def __str__(self):
        return self.name

    def __repr__(self):
        char = self.op.op_str
        parents = char.join(str(parent) for parent in self.parents)
        return f"{self.name} = {parents}"


@public
class FormulaAction(Action):
    """An execution of a formula, on some input points and parameters, with some outputs."""
    formula: "Formula"
    inputs: MutableMapping[str, Mod]
    input_points: List[Any]
    intermediates: MutableMapping[str, OpResult]
    outputs: MutableMapping[str, OpResult]
    output_points: List[Any]

    def __init__(self, formula: "Formula", *points: Any,
                 **inputs: Mod):
        super().__init__()
        self.formula = formula
        self.inputs = inputs
        self.intermediates = {}
        self.outputs = {}
        self.input_points = list(points)
        self.output_points = []

    def add_operation(self, op: CodeOp, value: Mod):
        parents: List[Union[Mod, OpResult]] = []
        for parent in {*op.variables, *op.parameters}:
            if parent in self.intermediates:
                parents.append(self.intermediates[parent])
            elif parent in self.inputs:
                parents.append(self.inputs[parent])
        self.intermediates[op.result] = OpResult(op.result, value, op.operator, *parents)

    def add_result(self, point: Any, **outputs: Mod):
        for k in outputs:
            self.outputs[k] = self.intermediates[k]
        self.output_points.append(point)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.formula}, {self.input_points}) = {self.output_points}"


class Formula(ABC):
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

    def __call__(self, *points: Any, **params: Mod) -> Tuple[Any, ...]:
        """
        Execute a formula.

        :param points: Points to pass into the formula.
        :param params: Parameters of the curve.
        :return: The resulting point(s).
        """
        from .point import Point
        if len(points) != self.num_inputs:
            raise ValueError(f"Wrong number of inputs for {self}.")
        coords = {}
        for i, point in enumerate(points):
            if point.coordinate_model != self.coordinate_model:
                raise ValueError(f"Wrong coordinate model of point {point}.")
            for coord, value in point.coords.items():
                coords[coord + str(i + 1)] = value
        locals = {**coords, **params}
        with FormulaAction(self, *points, **locals) as action:
            for op in self.code:
                op_result = op(**locals)
                action.add_operation(op, op_result)
                locals[op.result] = op_result
            result = []
            for i in range(self.num_outputs):
                ind = str(i + self.output_index)
                resulting = {}
                full_resulting = {}
                for variable in self.coordinate_model.variables:
                    full_variable = variable + ind
                    resulting[variable] = locals[full_variable]
                    full_resulting[full_variable] = locals[full_variable]
                point = Point(self.coordinate_model, **resulting)

                action.add_result(point, **full_resulting)
                result.append(point)
            return tuple(result)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name} for {self.coordinate_model})"

    @property
    @abstractmethod
    def input_index(self):
        """The starting index where this formula reads its inputs."""
        ...

    @property
    @abstractmethod
    def output_index(self) -> int:
        """The starting index where this formula stores its outputs."""
        ...

    @property
    @abstractmethod
    def inputs(self) -> Set[str]:
        """The input variables of the formula."""
        ...

    @property
    @abstractmethod
    def outputs(self) -> Set[str]:
        """The output variables of the formula."""
        ...

    @property
    def num_operations(self) -> int:
        """Number of operations."""
        return len(list(filter(lambda op: op.operator is not None, self.code)))

    @property
    def num_multiplications(self) -> int:
        """Number of multiplications."""
        return len(list(filter(lambda op: op.operator == OpType.Mult, self.code)))

    @property
    def num_divisions(self) -> int:
        """Number of divisions."""
        return len(list(filter(lambda op: op.operator == OpType.Div, self.code)))

    @property
    def num_inversions(self) -> int:
        """Number of inversions."""
        return len(list(filter(lambda op: op.operator == OpType.Inv, self.code)))

    @property
    def num_powers(self) -> int:
        """Number of powers."""
        return len(list(filter(lambda op: op.operator == OpType.Pow, self.code)))

    @property
    def num_squarings(self) -> int:
        """Number of squarings."""
        return len(list(filter(lambda op: op.operator == OpType.Sqr, self.code)))

    @property
    def num_addsubs(self) -> int:
        """Number of additions and subtractions."""
        return len(list(filter(lambda op: op.operator == OpType.Add or op.operator == OpType.Sub, self.code)))


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
                                                      range(self.output_index,
                                                            self.output_index + self.num_outputs)))

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
