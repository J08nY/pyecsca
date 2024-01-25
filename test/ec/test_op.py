from ast import parse

import pytest

from pyecsca.ec.formula import OpResult
from pyecsca.ec.mod import Mod
from pyecsca.ec.op import CodeOp, OpType


@pytest.mark.parametrize("name,module,result,op_type",
                         [("add", "x = a+b", "x = a+b", OpType.Add), ("sub", "x = a-b", "x = a-b", OpType.Sub),
                          ("mul", "y = a*b", "y = a*b", OpType.Mult), ("div", "z = a/b", "z = a/b", OpType.Div),
                          ("inv", "z = 1/b", "z = 1/b", OpType.Inv), ("pow", "b = a**d", "b = a^d", OpType.Pow),
                          ("sqr", "b = a**2", "b = a^2", OpType.Sqr), ("id1", "b = 7", "b = 7", OpType.Id),
                          ("id2", "b = a", "b = a", OpType.Id), ])
def test_str(name, module, result, op_type):
    code = parse(module, mode="exec")
    op = CodeOp(code)
    assert str(op) == result
    assert op.operator == op_type


@pytest.mark.parametrize("name,module,locals,result",
                         [("add", "x = a+b", {"a": Mod(5, 21), "b": Mod(7, 21)}, Mod(12, 21)),
                          ("sub", "x = a-b", {"a": Mod(7, 21), "b": Mod(5, 21)}, Mod(2, 21)), ])
def test_call(name, module, locals, result):
    code = parse(module, mode="exec")
    op = CodeOp(code)
    res = op(**locals)
    assert res == result


def test_opresult_repr():
    res = OpResult("a", Mod(7, 11), OpType.Neg, "b")
    assert repr(res) == "a = -b"
    res = OpResult("a", Mod(5, 7), OpType.Add, "c", 3)
    assert repr(res) == "a = c+3"
    res = OpResult("a", Mod(3, 11), OpType.Inv, "d")
    assert repr(res) == "a = 1/d"
