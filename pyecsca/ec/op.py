from ast import Module, walk, Name, BinOp, Constant, operator, Mult, Div, Add, Sub, Pow
from types import CodeType
from typing import FrozenSet, Optional

from .mod import Mod


class CodeOp(object):
    result: str
    parameters: FrozenSet[str]
    variables: FrozenSet[str]
    code: Module
    operator: Optional[operator]
    compiled: CodeType

    def __init__(self, code: Module):
        self.code = code
        assign = code.body[0]
        self.result = assign.targets[0].id
        params = set()
        variables = set()
        constants = set()
        op = None
        for node in walk(assign.value):
            if isinstance(node, Name):
                name = node.id
                if name.isupper():
                    variables.add(name)
                else:
                    params.add(name)
            elif isinstance(node, Constant):
                constants.add(node.value)
            elif isinstance(node, BinOp):
                op = node.op
                self.left = self.__to_name(node.left)
                self.right = self.__to_name(node.right)
        if op is None and len(constants) == 1:
            self.left = next(iter(constants))
            self.right = None
        self.operator = op
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

    def __to_opsymbol(self, op):
        if isinstance(op, Mult):
            return "*"
        elif isinstance(op, Div):
            return "/"
        elif isinstance(op, Add):
            return "+"
        elif isinstance(op, Sub):
            return "-"
        elif isinstance(op, Pow):
            return "^"
        return ""

    def __str__(self):
        return f"{self.result} = {self.left}{self.__to_opsymbol(self.operator)}{self.right}"

    def __repr__(self):
        return f"CodeOp({self.result} = f(params={self.parameters}, vars={self.variables}, consts={self.constants}))"

    def __call__(self, *args, **kwargs: Mod) -> Mod:
        """Execute this operation with kwargs."""
        loc = dict(kwargs)
        exec(self.compiled, {}, loc)
        return loc[self.result]
