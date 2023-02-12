"""Provides an abstract base class of a formula along with concrete instantiations."""
from abc import ABC, abstractmethod
from ast import parse, Expression
from functools import cached_property

from astunparse import unparse
from itertools import product
from typing import List, Set, Any, ClassVar, MutableMapping, Tuple, Union, Dict

from pkg_resources import resource_stream
from public import public
from sympy import sympify, FF, symbols, Poly, Rational

from .context import ResultAction
from . import context
from .error import UnsatisfiedAssumptionError, raise_unsatisified_assumption
from .mod import Mod, SymbolicMod
from .op import CodeOp, OpType
from ..misc.cfg import getconfig


@public
class OpResult:
    """Result of an operation."""

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
class FormulaAction(ResultAction):
    """Execution of a formula, on some input points and parameters, with some outputs."""

    formula: "Formula"
    """The formula that was executed."""
    inputs: MutableMapping[str, Mod]
    """The input variables (point coordinates and parameters)."""
    input_points: List[Any]
    """The input points."""
    intermediates: MutableMapping[str, List[OpResult]]
    """Intermediates computed during execution."""
    outputs: MutableMapping[str, OpResult]
    """The output variables."""
    output_points: List[Any]
    """The output points."""

    def __init__(self, formula: "Formula", *points: Any, **inputs: Mod):
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
                parents.append(self.intermediates[parent][-1])
            elif parent in self.inputs:
                parents.append(self.inputs[parent])
        li = self.intermediates.setdefault(op.result, [])
        li.append(OpResult(op.result, value, op.operator, *parents))

    def add_result(self, point: Any, **outputs: Mod):
        for k in outputs:
            self.outputs[k] = self.intermediates[k][-1]
        self.output_points.append(point)

    def __str__(self):
        return f"{self.__class__.__name__}({self.formula})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.formula}, {self.input_points}) = {self.output_points}"


@public
class Formula(ABC):
    """Formula operating on points."""

    name: str
    """Name of the formula."""
    shortname: ClassVar[str]
    """A shortname for the type of the formula."""
    coordinate_model: Any
    """Coordinate model of the formula."""
    meta: MutableMapping[str, Any]
    """Meta information about the formula, such as its source."""
    parameters: List[str]
    """Formula parameters (i.e. new parameters introduced by the formula, like `half = 1/2`)."""
    assumptions: List[Expression]
    """Assumptions of the formula (e.g. `Z1 == 1` or `2*half == 1`)."""
    code: List[CodeOp]
    """The collection of ops that constitute the code of the formula."""
    num_inputs: ClassVar[int]
    """Number of inputs (points) of the formula."""
    num_outputs: ClassVar[int]
    """Number of outputs (points) of the formula."""
    unified: bool
    """Whether the formula is specifies that it is unified."""

    @cached_property
    def assumptions_str(self):
        return [unparse(assumption)[1:-2] for assumption in self.assumptions]

    def __validate_params(self, field, params):
        for key, value in params.items():
            if not isinstance(value, Mod) or value.n != field:
                raise ValueError(f"Wrong param input {key} = {value}.")

    def __validate_points(self, field, points, params):
        # Validate number of inputs.
        if len(points) != self.num_inputs:
            raise ValueError(f"Wrong number of inputs for {self}.")
        # Validate input points and unroll them into input params.
        for i, point in enumerate(points):
            if point.coordinate_model != self.coordinate_model:
                raise ValueError(f"Wrong coordinate model of point {point}.")
            for coord, value in point.coords.items():
                if not isinstance(value, Mod) or value.n != field:
                    raise ValueError(
                        f"Wrong coordinate input {coord} = {value} of point {i}."
                    )
                params[coord + str(i + 1)] = value

    def __validate_assumptions(self, field, params):
        # Validate assumptions and compute formula parameters.
        # TODO: Should this also validate coordinate assumptions and compute their parameters?
        is_symbolic = any(isinstance(x, SymbolicMod) for x in params.values())
        for assumption, assumption_string in zip(self.assumptions, self.assumptions_str):
            lhs, rhs = assumption_string.split(" == ")
            if lhs in params:
                # Handle an assumption check on value of input points.
                alocals: Dict[str, Union[Mod, int]] = {**params}
                compiled = compile(assumption, "", mode="eval")
                holds = eval(compiled, None, alocals)
                if not holds:
                    # The assumption doesn't hold, see what is the current configured action and do it.
                    raise_unsatisified_assumption(
                        getconfig().ec.unsatisfied_formula_assumption_action,
                        f"Unsatisfied assumption in the formula ({assumption_string}).",
                    )
            elif lhs in self.parameters and is_symbolic:
                # Handle a symbolic assignment to a new parameter.
                k = FF(field)
                expr = sympify(rhs, evaluate=False)
                for curve_param, value in params.items():
                    if isinstance(value, SymbolicMod):
                        expr = expr.subs(curve_param, value.x)
                    else:
                        expr = expr.subs(curve_param, k(value))
                params[lhs] = SymbolicMod(expr, field)
            else:
                k = FF(field)
                expr = sympify(f"{rhs} - {lhs}", evaluate=False)
                for curve_param, value in params.items():
                    if isinstance(value, SymbolicMod):
                        expr = expr.subs(curve_param, value.x)
                    else:
                        expr = expr.subs(curve_param, k(value))
                if (
                    len(expr.free_symbols) > 1
                    or (param := str(expr.free_symbols.pop())) not in self.parameters
                ):
                    raise ValueError(
                        f"This formula couldn't be executed due to an unsupported assumption ({assumption_string})."
                    )

                def resolve(expression, k):
                    if not expression.args:
                        return expression
                    args = []
                    for arg in expression.args:
                        if isinstance(arg, Rational):
                            a = arg.p
                            b = arg.q
                            res = k(a) / k(b)
                        else:
                            res = resolve(arg, k)
                        args.append(res)
                    return expression.func(*args)

                expr = resolve(expr, k)
                poly = Poly(expr, symbols(param), domain=k)
                roots = poly.ground_roots()
                for root in roots:
                    params[param] = Mod(int(root), field)
                    break
                else:
                    raise UnsatisfiedAssumptionError(
                        f"Unsatisfied assumption in the formula ({assumption_string}).\n"
                        f"'{expr}' has no roots in the base field {k}."
                    )

    def __call__(self, field: int, *points: Any, **params: Mod) -> Tuple[Any, ...]:
        """
        Execute a formula.

        :param field: The field over which the computation is performed.
        :param points: Points to pass into the formula.
        :param params: Parameters of the curve.
        :return: The resulting point(s).
        """
        from .point import Point

        self.__validate_params(field, params)
        self.__validate_points(field, points, params)
        if self.assumptions:
            self.__validate_assumptions(field, params)
        # Execute the actual formula.
        with FormulaAction(self, *points, **params) as action:
            for op in self.code:
                op_result = op(**params)
                # This check and cast fixes the issue when the op is `Z3 = 1`.
                # TODO: This is not general enough, if for example the op is `t = 1/2`, it will be float.
                #       Temporarily, add an assertion that this does not happen so we do not give bad results.
                if isinstance(op_result, float):
                    raise AssertionError(
                        f"Bad stuff happened in op {op}, floats will pollute the results."
                    )
                if not isinstance(op_result, Mod):
                    op_result = Mod(op_result, field)
                if context.current is not None:
                    action.add_operation(op, op_result)
                params[op.result] = op_result
            result = []
            # Go over the outputs and construct the resulting points.
            for i in range(self.num_outputs):
                ind = str(i + self.output_index)
                resulting = {}
                full_resulting = {}
                for variable in self.coordinate_model.variables:
                    full_variable = variable + ind
                    resulting[variable] = params[full_variable]
                    full_resulting[full_variable] = params[full_variable]
                point = Point(self.coordinate_model, **resulting)

                if context.current is not None:
                    action.add_result(point, **full_resulting)
                result.append(point)
            return action.exit(tuple(result))

    def __str__(self):
        return f"{self.shortname}[{self.name}]"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name} for {self.coordinate_model})"

    @property
    @abstractmethod
    def input_index(self):
        """Return the starting index where this formula reads its inputs."""
        raise NotImplementedError

    @property
    @abstractmethod
    def output_index(self) -> int:
        """Return the starting index where this formula stores its outputs."""
        raise NotImplementedError

    @property
    @abstractmethod
    def inputs(self) -> Set[str]:
        """Return the input variables of the formula."""
        raise NotImplementedError

    @property
    @abstractmethod
    def outputs(self) -> Set[str]:
        """Return the output variables of the formula."""
        raise NotImplementedError

    @property
    def num_operations(self) -> int:
        """Return the number of operations."""
        return len(list(filter(lambda op: op.operator is not None, self.code)))

    @property
    def num_multiplications(self) -> int:
        """Return the number of multiplications."""
        return len(list(filter(lambda op: op.operator == OpType.Mult, self.code)))

    @property
    def num_divisions(self) -> int:
        """Return the number of divisions."""
        return len(list(filter(lambda op: op.operator == OpType.Div, self.code)))

    @property
    def num_inversions(self) -> int:
        """Return the number of inversions."""
        return len(list(filter(lambda op: op.operator == OpType.Inv, self.code)))

    @property
    def num_powers(self) -> int:
        """Return the number of powers."""
        return len(list(filter(lambda op: op.operator == OpType.Pow, self.code)))

    @property
    def num_squarings(self) -> int:
        """Return the number of squarings."""
        return len(list(filter(lambda op: op.operator == OpType.Sqr, self.code)))

    @property
    def num_addsubs(self) -> int:
        """Return the number of additions and subtractions."""
        return len(
            list(filter(lambda op: op.operator in (OpType.Add, OpType.Sub), self.code))
        )


class EFDFormula(Formula):
    """Formula from the `Explicit-Formulas Database <https://www.hyperelliptic.org/EFD/>`_."""

    def __init__(self, path: str, name: str, coordinate_model: Any):
        self.name = name
        self.coordinate_model = coordinate_model
        self.meta = {}
        self.parameters = []
        self.assumptions = []
        self.code = []
        self.unified = False
        self.__read_meta_file(path)
        self.__read_op3_file(path + ".op3")

    def __read_meta_file(self, path):
        with resource_stream(__name__, path) as f:
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

    def __read_op3_file(self, path):
        with resource_stream(__name__, path) as f:
            for line in f.readlines():
                code_module = parse(
                    line.decode("ascii").replace("^", "**"), path, mode="exec"
                )
                self.code.append(CodeOp(code_module))

    @property
    def input_index(self):
        return 1

    @property
    def output_index(self):
        return max(self.num_inputs + 1, 3)

    @property
    def inputs(self):
        return {
            var + str(i)
            for var, i in product(
                self.coordinate_model.variables, range(1, 1 + self.num_inputs)
            )
        }

    @property
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
        return hash(self.name) + hash(self.coordinate_model)


@public
class AdditionFormula(Formula, ABC):
    """Formula that adds two points."""

    shortname = "add"
    num_inputs = 2
    num_outputs = 1


@public
class AdditionEFDFormula(AdditionFormula, EFDFormula):
    pass


@public
class DoublingFormula(Formula, ABC):
    """Formula that doubles a point."""

    shortname = "dbl"
    num_inputs = 1
    num_outputs = 1


@public
class DoublingEFDFormula(DoublingFormula, EFDFormula):
    pass


@public
class TriplingFormula(Formula, ABC):
    """Formula that triples a point."""

    shortname = "tpl"
    num_inputs = 1
    num_outputs = 1


@public
class TriplingEFDFormula(TriplingFormula, EFDFormula):
    pass


@public
class NegationFormula(Formula, ABC):
    """Formula that negates a point."""

    shortname = "neg"
    num_inputs = 1
    num_outputs = 1


@public
class NegationEFDFormula(NegationFormula, EFDFormula):
    pass


@public
class ScalingFormula(Formula, ABC):
    """Formula that somehow scales the point (to a given representative of a projective class)."""

    shortname = "scl"
    num_inputs = 1
    num_outputs = 1


@public
class ScalingEFDFormula(ScalingFormula, EFDFormula):
    pass


@public
class DifferentialAdditionFormula(Formula, ABC):
    """
    Differential addition formula that adds two points with a known difference.

    The first input point is the difference of the third input and the second input (`P[0] = P[2] - P[1]`).
    """

    shortname = "dadd"
    num_inputs = 3
    num_outputs = 1


@public
class DifferentialAdditionEFDFormula(DifferentialAdditionFormula, EFDFormula):
    pass


@public
class LadderFormula(Formula, ABC):
    """
    Ladder formula for simultaneous addition of two points and doubling of the one of them, with a known difference.

    The first input point is the difference of the third input and the second input (`P[0] = P[2] - P[1]`).
    The first output point is the doubling of the second input point (`O[0] = 2 * P[1]`).
    The second output point is the addition of the second and third input points (`O[1] = P[1] + P[2]`).
    """

    shortname = "ladd"
    num_inputs = 3
    num_outputs = 2


@public
class LadderEFDFormula(LadderFormula, EFDFormula):
    pass
