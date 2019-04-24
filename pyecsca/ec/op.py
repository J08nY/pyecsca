from ast import Module, walk, Name, BinOp, operator
from types import CodeType
from typing import FrozenSet, Optional

from .mod import Mod


class Op(object):
    result: str
    parameters: FrozenSet[str]
    variables: FrozenSet[str]

    def __call__(self, *args, **kwargs: Mod) -> Mod:
        """Execute this operation with kwargs."""
        raise NotImplementedError


class CodeOp(Op):
    code: Module
    operator: Optional[operator]
    compiled: CodeType

    def __init__(self, code: Module):
        self.code = code
        assign = code.body[0]
        self.result = assign.targets[0].id
        params = set()
        variables = set()
        op = None
        for node in walk(assign.value):
            if isinstance(node, Name):
                name = node.id
                if name.isupper():
                    variables.add(name)
                else:
                    params.add(name)
            elif isinstance(node, BinOp):
                op = node.op
        self.operator = op
        self.parameters = frozenset(params)
        self.variables = frozenset(variables)
        self.compiled = compile(self.code, "", mode="exec")

    def __repr__(self):
        return f"CodeOp({self.result} = f(params={self.parameters}, vars={self.variables}))"

    def __call__(self, *args, **kwargs: Mod) -> Mod:
        loc = dict(kwargs)
        exec(self.compiled, {}, loc)
        return loc[self.result]
