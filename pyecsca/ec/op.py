from ast import Module, walk, Name
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

    def __call__(self, *args, **kwargs) -> Mod:
        loc = dict(kwargs)
        exec(compile(self.code, "", mode="exec"), {}, loc)
        return loc[self.result]
