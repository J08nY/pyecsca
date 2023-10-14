"""Provides a class for a code operation."""
from ast import (
    Module,
    walk,
    Name,
    BinOp,
    UnaryOp,
    Constant,
    Mult,
    Div,
    Add,
    Sub,
    Pow,
    Assign,
    operator as ast_operator,
    unaryop as ast_unaryop,
    USub,
    parse,
)
from enum import Enum
from types import CodeType
from typing import FrozenSet, cast, Any, Optional, Union, Tuple

from astunparse import unparse
from public import public

from .mod import Mod


@public
class OpType(Enum):
    """Type of binary and unary operators."""

    Add = (2, "+")
    Sub = (2, "-")
    Neg = (1, "-")
    Mult = (2, "*")
    Div = (2, "/")
    Inv = (1, "/")
    Sqr = (1, "^")
    Pow = (2, "^")
    Id = (1, "")

    def __init__(self, num_inputs: int, op_str: str):
        self.num_inputs = num_inputs
        self.op_str = op_str


@public
class CodeOp:
    """Operation that can be executed."""

    result: str
    """The result variable of the operation (e.g. the `r` in `r = 2*a`)."""
    parameters: FrozenSet[str]
    """The parameters used in the operation (e.g. `a`, `b`)."""
    variables: FrozenSet[str]
    """The variables used in the operation (e.g. `X1`, `Z2`)."""
    constants: FrozenSet[int]  # TODO: Might not be only int? See issue in Formula eval.
    """The constants used in the operation."""
    code: Module
    """The code of the operation."""
    operator: OpType
    """The operator type that executes in the operation."""
    compiled: CodeType
    """The compiled code of the operation."""

    def __init__(self, code: Module):
        self.code = code
        assign = cast(Assign, code.body[0])
        self.result = cast(Name, assign.targets[0]).id
        params = set()
        variables = set()
        constants = set()
        op: Optional[Union[ast_operator, ast_unaryop]] = None
        self.left = None
        self.right = None
        for node in walk(assign.value):
            if isinstance(node, Name):
                name = node.id
                if name.isupper():
                    variables.add(name)
                else:
                    params.add(name)
            elif isinstance(node, Constant):
                constants.add(node.value)
        if isinstance(assign.value, BinOp):
            op = assign.value.op
            self.left = self.__to_name(assign.value.left)
            self.right = self.__to_name(assign.value.right)
        elif isinstance(assign.value, UnaryOp):
            op = assign.value.op
            self.right = self.__to_name(assign.value.operand)
        elif isinstance(assign.value, Name):
            self.left = assign.value.id
        elif isinstance(assign.value, Constant):
            self.left = assign.value.value
        self.operator = self.__to_op(op, self.left, self.right)
        self.parameters = frozenset(params)
        self.variables = frozenset(variables)
        self.constants = frozenset(constants)
        self.compiled = compile(self.code, "", mode="exec")

    def __to_name(self, node):
        if isinstance(node, Name):
            return node.id
        elif isinstance(node, Constant):
            return node.value
        else:
            return None

    def __to_op(
        self, op: Optional[Union[ast_operator, ast_unaryop]], left: Any, right: Any
    ) -> OpType:
        if isinstance(op, Mult):
            return OpType.Mult
        elif isinstance(op, Div):
            if left == 1:
                return OpType.Inv
            return OpType.Div
        elif isinstance(op, Add):
            return OpType.Add
        elif isinstance(op, Sub):
            return OpType.Sub
        elif isinstance(op, USub):
            return OpType.Neg
        elif isinstance(op, Pow):
            if right == 2:
                return OpType.Sqr
            return OpType.Pow
        return OpType.Id

    @property
    def parents(self) -> Tuple[Union[str, int]]:
        if self.operator in (OpType.Inv, OpType.Neg):
            return (self.right,)  # type: ignore
        elif self.operator in (OpType.Sqr, OpType.Id):
            return (self.left,)  # type: ignore
        else:
            return self.left, self.right  # type: ignore

    def __getstate__(self):
        state = self.__dict__.copy()
        state["code"] = unparse(state["code"])
        del state["compiled"]
        return state

    def __setstate__(self, state):
        state["code"] = parse(state["code"], mode="exec")
        state["compiled"] = compile(state["code"], "", mode="exec")
        self.__dict__.update(state)

    def __str__(self):
        return f"{self.result} = {self.left if self.left is not None else ''}{self.operator.op_str}{self.right if self.right is not None else ''}"

    def __repr__(self):
        return f"CodeOp({self.result} = f(params={self.parameters}, vars={self.variables}, consts={self.constants}))"

    def __call__(self, *args, **kwargs: Mod) -> Mod:
        """Execute this operation with :paramref:`.__call__.kwargs`."""
        exec(self.compiled, None, kwargs)
        return kwargs[self.result]
