"""Provides an abstract base class of a formula."""
from abc import ABC
from ast import Expression
from functools import cached_property
from itertools import product

from astunparse import unparse
from typing import List, Any, ClassVar, MutableMapping, Tuple, Union, Dict

from public import public
from sympy import FF, symbols, Poly

from pyecsca.ec.context import ResultAction
from pyecsca.ec import context
from pyecsca.ec.error import UnsatisfiedAssumptionError, raise_unsatisified_assumption
from pyecsca.ec.mod import Mod, mod, SymbolicMod
from pyecsca.ec.op import CodeOp, OpType
from pyecsca.misc.cfg import getconfig
from pyecsca.misc.cache import sympify


@public
class OpResult:
    """Result of an operation."""

    parents: Tuple
    op: OpType
    name: str
    value: Mod

    def __init__(self, name: str, value: Mod, op: OpType, *parents: Any):
        if len(parents) != op.num_inputs:
            raise ValueError(
                f"Wrong number of parents ({len(parents)}) to OpResult: {op} ({op.num_inputs})."
            )
        self.parents = tuple(parents)
        self.name = name
        self.value = value
        self.op = op

    def __str__(self):
        return self.name

    def __repr__(self):
        char = self.op.op_str
        if self.op == OpType.Inv:
            parents = "1" + char + str(self.parents[0])
        elif self.op == OpType.Neg:
            parents = char + str(self.parents[0])
        else:
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
    op_results: List[OpResult]
    """The intermediates but ordered as they were computed."""
    outputs: MutableMapping[str, OpResult]
    """The output variables."""
    output_points: List[Any]
    """The output points."""

    def __init__(self, formula: "Formula", *points: Any, **inputs: Mod):
        super().__init__()
        self.formula = formula
        self.inputs = inputs
        self.intermediates = {}
        self.op_results = []
        self.outputs = {}
        self.input_points = list(points)
        self.output_points = []

    def add_operation(self, op: CodeOp, value: Mod):
        parents: List[Union[int, Mod, OpResult]] = []
        for parent in op.parents:
            if isinstance(parent, str):
                if parent in self.intermediates:
                    parents.append(self.intermediates[parent][-1])
                elif parent in self.inputs:
                    parents.append(self.inputs[parent])
            else:
                parents.append(parent)
        result = OpResult(op.result, value, op.operator, *parents)
        li = self.intermediates.setdefault(op.result, [])
        li.append(result)
        self.op_results.append(result)

    def add_result(self, point: Any, **outputs: Mod):
        for k in outputs:
            self.outputs[k] = self.intermediates[k][-1]
        self.output_points.append(point)

    def __str__(self):
        return f"{self.__class__.__name__}({self.formula})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.formula}, {self.input_points}) = {self.output_points}"


_assumption_cache: Dict[Tuple[str, str, FF, Tuple[Mod, ...]], Mod] = {}


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
    """Whether the formula specifies that it is unified."""

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

    def __validate_assumption_point(self, assumption, params):
        # Handle an assumption check on value of input points.
        alocals: Dict[str, Union[Mod, int]] = {**params}
        compiled = compile(assumption, "", mode="eval")
        holds = eval(compiled, None, alocals)  # eval is OK here, skipcq: PYL-W0123
        return holds

    def __validate_assumption_simple(self, lhs, rhs, field, params):
        # Handle a simple parameter assignment (lhs is an unassigned parameter of the formula).
        expr = sympify(rhs, evaluate=False)
        used_symbols = sorted(expr.free_symbols)
        used_params = []
        for symbol in used_symbols:
            if (value := params.get(symbol.name, None)) is not None:
                used_params.append(value)
                if isinstance(value, SymbolicMod):
                    expr = expr.xreplace({symbol: value.x})
                else:
                    expr = expr.xreplace({symbol: int(value)})
            else:
                return False
        cache_key = (lhs, rhs, field, tuple(used_params))
        if cache_key in _assumption_cache:
            params[lhs] = _assumption_cache[cache_key]
        else:
            if any(isinstance(x, SymbolicMod) for x in params.values()):
                params[lhs] = SymbolicMod(expr, field)
            else:
                domain = FF(field)
                numerator, denominator = expr.as_numer_denom()
                val = int(domain.from_sympy(numerator) / domain.from_sympy(denominator))
                params[lhs] = mod(val, field)
            _assumption_cache[cache_key] = params[lhs]
        return True

    def __validate_assumption_generic(self, lhs, rhs, field, params, assumption_string):
        # Handle a generic parameter assignment (parameter may be anyway in the assumption).
        expr = sympify(f"{rhs} - {lhs}", evaluate=False)
        remaining = []
        for symbol in expr.free_symbols:
            if (value := params.get(symbol.name, None)) is not None:
                if isinstance(value, SymbolicMod):
                    expr = expr.xreplace({symbol: value.x})
                else:
                    expr = expr.xreplace({symbol: int(value)})
            else:
                remaining.append(symbol)
        if len(remaining) > 1 or (param := remaining[0].name) not in self.parameters:
            raise ValueError(
                f"This formula couldn't be executed due to an unsupported assumption ({assumption_string})."
            )
        numerator, _ = expr.as_numer_denom()
        domain = FF(field)
        poly = Poly(numerator, symbols(param), domain=domain)
        roots = poly.ground_roots()
        for root in roots:
            params[param] = mod(int(domain.from_sympy(root)), field)
            return
        raise UnsatisfiedAssumptionError(
            f"Unsatisfied assumption in the formula ({assumption_string}).\n"
            f"'{expr}' has no roots in the base field GF({field})."
        )

    def __validate_assumptions(self, field, params):
        # Validate assumptions and compute formula parameters.
        # TODO: Should this also validate coordinate assumptions and compute their parameters?
        for assumption, assumption_string in zip(
            self.assumptions, self.assumptions_str
        ):
            lhs, rhs = assumption_string.split(" == ")
            if lhs in params:
                if not self.__validate_assumption_point(assumption, params):
                    raise_unsatisified_assumption(
                        getconfig().ec.unsatisfied_formula_assumption_action,
                        f"Unsatisfied assumption in the formula ({assumption_string}).",
                    )
            elif lhs in self.parameters:
                if not self.__validate_assumption_simple(lhs, rhs, field, params):
                    raise_unsatisified_assumption(
                        getconfig().ec.unsatisfied_formula_assumption_action,
                        f"Unsatisfied assumption in the formula ({assumption_string}).",
                    )
            else:
                self.__validate_assumption_generic(
                    lhs, rhs, field, params, assumption_string
                )

    def __call__(self, field: int, *points: Any, **params: Mod) -> Tuple[Any, ...]:
        """
        Execute a formula.

        :param field: The field over which the computation is performed.
        :param points: Points to pass into the formula.
        :param params: Parameters of the curve.
        :return: The resulting point(s).
        """
        from pyecsca.ec.point import Point

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
                    op_result = mod(op_result, field)
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

    def __lt__(self, other):
        if not isinstance(other, Formula):
            raise TypeError("Cannot compare.")
        if self.name is None:
            return True
        if other.name is None:
            return False
        return self.name < other.name

    def __str__(self):
        return f"{self.coordinate_model!s}/{self.name}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name} for {self.coordinate_model})"

    @cached_property
    def input_index(self):
        """Return the starting index where this formula reads its inputs."""
        return 1

    @cached_property
    def output_index(self):
        """Return the starting index where this formula stores its outputs."""
        return max(self.num_inputs + 1, 3)

    @cached_property
    def inputs(self):
        """Return the input variables of the formula."""
        return {
            var + str(i)
            for var, i in product(
                self.coordinate_model.variables, range(1, 1 + self.num_inputs)
            )
        }

    @cached_property
    def outputs(self):
        """Return the output variables of the formula."""
        return {
            var + str(i)
            for var, i in product(
                self.coordinate_model.variables,
                range(self.output_index, self.output_index + self.num_outputs),
            )
        }

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


@public
class AdditionFormula(Formula, ABC):
    """Formula that adds two points."""

    shortname = "add"
    num_inputs = 2
    num_outputs = 1


@public
class DoublingFormula(Formula, ABC):
    """Formula that doubles a point."""

    shortname = "dbl"
    num_inputs = 1
    num_outputs = 1


@public
class TriplingFormula(Formula, ABC):
    """Formula that triples a point."""

    shortname = "tpl"
    num_inputs = 1
    num_outputs = 1


@public
class NegationFormula(Formula, ABC):
    """Formula that negates a point."""

    shortname = "neg"
    num_inputs = 1
    num_outputs = 1


@public
class ScalingFormula(Formula, ABC):
    """Formula that somehow scales the point (to a given representative of a projective class)."""

    shortname = "scl"
    num_inputs = 1
    num_outputs = 1


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
