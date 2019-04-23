import ast
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import List, Tuple, Optional, Union, MutableMapping, Any, Mapping

from public import public

from .formula import Formula
from .mod import Mod
from .op import CodeOp
from .point import Point


@public
class OpResult(object):
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
    formula: Formula
    input_points: List[Point]
    inputs: MutableMapping[str, Mod]
    intermediates: MutableMapping[str, Union[Mod, OpResult]]
    roots: MutableMapping[str, OpResult]
    output_points: List[Point]

    def __init__(self, formula: Formula, *points: Point, **inputs: Mod):
        self.formula = formula
        self.input_points = list(points)
        self.inputs = inputs
        self.intermediates = {}
        self.roots = {}
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
            self.roots[k] = self.intermediates[k]
        self.output_points.append(point)

    def __repr__(self):
        return f"Action({self.formula}, {self.input_points}) = {self.output_points}"


@public
class Context(object):
    def _log_action(self, formula: Formula, *points: Point, **inputs: Mod):
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
        self._log_action(formula, *points, **locals)
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
        return self._execute(formula, *points, **params)

    def __str__(self):
        return self.__class__.__name__


@public
class NullContext(Context):

    def _log_action(self, formula: Formula, *points: Point, **inputs: Mod):
        pass

    def _log_operation(self, op: CodeOp, value: Mod):
        pass

    def _log_result(self, point: Point, **outputs: Mod):
        pass


@public
class DefaultContext(Context):
    actions: List[Action]

    def __init__(self):
        self.actions = []

    def _log_action(self, formula: Formula, *points: Point, **inputs: Mod):
        self.actions.append(Action(formula, *points, **inputs))

    def _log_operation(self, op: CodeOp, value: Mod):
        self.actions[-1].add_operation(op, value)

    def _log_result(self, point: Point, **outputs: Mod):
        self.actions[-1].add_result(point, **outputs)


_actual_context: ContextVar[Context] = ContextVar("operational_context", default=NullContext())


class ContextManager(object):
    def __init__(self, new_context):
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Context:
        self.saved_context = getcontext()
        setcontext(self.new_context)
        return self.new_context

    def __exit__(self, t, v, tb):
        setcontext(self.saved_context)


@public
def getcontext():
    return _actual_context.get()


@public
def setcontext(ctx: Context) -> Token:
    return _actual_context.set(ctx)


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    if ctx is None:
        ctx = getcontext()
    return ContextManager(ctx)
