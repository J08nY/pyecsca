from ast import Module, walk, Name
from types import CodeType
from typing import FrozenSet

from .mod import Mod


class Op(object):
    result: str
    parameters: FrozenSet[str]
    variables: FrozenSet[str]

    def __call__(self, *args, **kwargs) -> Mod:
        raise NotImplementedError


class CodeOp(Op):
    code: Module
    compiled: CodeType

    def __init__(self, code: Module):
        self.code = code
        assign = code.body[0]
        self.result = assign.targets[0].id
        params = set()
        variables = set()
        for node in walk(assign.value):
            if isinstance(node, Name):
                name = node.id
                if name.isupper():
                    variables.add(name)
                else:
                    params.add(name)
        self.parameters = frozenset(params)
        self.variables = frozenset(variables)
        self.compiled = compile(self.code, "", mode="exec")

    def __repr__(self):
        return f"CodeOp({self.result} = f(params={self.parameters}, vars={self.variables}))"

    def __call__(self, *args, **kwargs) -> Mod:
        loc = dict(kwargs)
        exec(self.compiled, {}, loc)
        return loc[self.result]
