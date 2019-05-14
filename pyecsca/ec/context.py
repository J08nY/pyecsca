import ast
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import List, Tuple, Optional, Union, MutableMapping, Any, ContextManager

from public import public

from .formula import Formula
from .mod import Mod
from .op import CodeOp
from .point import Point


@public
class OpResult(object):
    """A result of an operation."""
    parents: Tuple
    op: ast.operator
    name: str
    value: Mod

    def __init__(self, name: str, value: Mod, op: ast.operator, *parents: Any):
        self.parents = tuple(parents)
        self.name = name
        self.value = value
        self.op = op

    def __str__(self):
        return self.name

    def __repr__(self):
        char = ""
        if isinstance(self.op, ast.Mult):
            char = "*"
        elif isinstance(self.op, ast.Add):
            char = "+"
        elif isinstance(self.op, ast.Sub):
            char = "-"
        elif isinstance(self.op, ast.Div):
            char = "/"
        parents = char.join(str(parent) for parent in self.parents)
        return f"{self.name} = {parents}"


@public
class Action(object):
    """An execution of some operations with inputs and outputs."""
    inputs: MutableMapping[str, Mod]
    input_points: List[Point]
    intermediates: MutableMapping[str, Union[Mod, OpResult]]
    outputs: MutableMapping[str, OpResult]
    output_points: List[Point]

    def __init__(self, *points: Point, **inputs: Mod):
        self.inputs = inputs
        self.intermediates = {}
        self.outputs = {}
        self.input_points = list(points)
        self.output_points = []

    def add_operation(self, op: CodeOp, value: Mod):
        parents = []
        for parent in {*op.variables, *op.parameters}:
            if parent in self.intermediates:
                parents.append(self.intermediates[parent])
            elif parent in self.inputs:
                parents.append(self.inputs[parent])
        self.intermediates[op.result] = OpResult(op.result, value, op.operator, *parents)

    def add_result(self, point: Point, **outputs: Mod):
        for k in outputs:
            self.outputs[k] = self.intermediates[k]
        self.output_points.append(point)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.input_points}) = {self.output_points}"


@public
class FormulaAction(Action):
    """An execution of a formula, on some input points and parameters, with some outputs."""
    formula: Formula

    def __init__(self, formula: Formula, *points: Point, **inputs: Mod):
        super().__init__(*points, **inputs)
        self.formula = formula

    def __repr__(self):
        return f"{self.__class__.__name__}({self.formula}, {self.input_points}) = {self.output_points}"


@public
class Context(object):
    def _log_formula(self, formula: Formula, *points: Point, **inputs: Mod):
        raise NotImplementedError

    def _log_operation(self, op: CodeOp, value: Mod):
        raise NotImplementedError

    def _log_result(self, point: Point, **outputs: Mod):
        raise NotImplementedError

    def _execute(self, formula: Formula, *points: Point, **params: Mod) -> Tuple[Point, ...]:
        if len(points) != formula.num_inputs:
            raise ValueError(f"Wrong number of inputs for {formula}.")
        coords = {}
        for i, point in enumerate(points):
            if point.coordinate_model != formula.coordinate_model:
                raise ValueError(f"Wrong coordinate model of point {point}.")
            for coord, value in point.coords.items():
                coords[coord + str(i + 1)] = value
        locals = {**coords, **params}
        self._log_formula(formula, *points, **locals)
        for op in formula.code:
            op_result = op(**locals)
            self._log_operation(op, op_result)
            locals[op.result] = op_result
        result = []
        for i in range(formula.num_outputs):
            ind = str(i + formula.output_index)
            resulting = {}
            full_resulting = {}
            for variable in formula.coordinate_model.variables:
                full_variable = variable + ind
                resulting[variable] = locals[full_variable]
                full_resulting[full_variable] = locals[full_variable]
            point = Point(formula.coordinate_model, **resulting)

            self._log_result(point, **full_resulting)
            result.append(point)
        return tuple(result)

    def execute(self, formula: Formula, *points: Point, **params: Mod) -> Tuple[Point, ...]:
        """
        Execute a formula.

        :param formula: Formula to execute.
        :param points: Points to pass into the formula.
        :param params: Parameters of the curve.
        :return: The resulting point(s).
        """
        return self._execute(formula, *points, **params)

    def __str__(self):
        return self.__class__.__name__


@public
class NullContext(Context):
    """A context that does not trace any operations."""

    def _log_formula(self, formula: Formula, *points: Point, **inputs: Mod):
        pass

    def _log_operation(self, op: CodeOp, value: Mod):
        pass

    def _log_result(self, point: Point, **outputs: Mod):
        pass


@public
class DefaultContext(Context):
    """A context that traces executions of formulas."""
    actions: List[FormulaAction]

    def __init__(self):
        self.actions = []

    def _log_formula(self, formula: Formula, *points: Point, **inputs: Mod):
        self.actions.append(FormulaAction(formula, *points, **inputs))

    def _log_operation(self, op: CodeOp, value: Mod):
        self.actions[-1].add_operation(op, value)

    def _log_result(self, point: Point, **outputs: Mod):
        self.actions[-1].add_result(point, **outputs)


_actual_context: ContextVar[Context] = ContextVar("operational_context", default=NullContext())


class _ContextManager(object):
    def __init__(self, new_context):
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Context:
        self.token = setcontext(self.new_context)
        return self.new_context

    def __exit__(self, t, v, tb):
        resetcontext(self.token)


@public
def getcontext() -> Context:
    """Get the current thread/task context."""
    return _actual_context.get()


@public
def setcontext(ctx: Context) -> Token:
    """
    Set the current thread/task context.

    :param ctx: A context to set.
    :return: A token to restore previous context.
    """
    return _actual_context.set(ctx)


@public
def resetcontext(token: Token):
    """
    Reset the context to a previous value.

    :param token: A token to restore.
    """
    _actual_context.reset(token)


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    """
    Use a local context.

    :param ctx: If none, current context is copied.
    :return: A context manager.
    """
    if ctx is None:
        ctx = getcontext()
    return _ContextManager(ctx)
