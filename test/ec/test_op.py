from ast import parse
from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.formula import OpResult
from pyecsca.ec.mod import Mod
from pyecsca.ec.op import CodeOp, OpType


class OpTests(TestCase):
    @parameterized.expand(
        [
            ("add", "x = a+b", "x = a+b", OpType.Add),
            ("sub", "x = a-b", "x = a-b", OpType.Sub),
            ("mul", "y = a*b", "y = a*b", OpType.Mult),
            ("div", "z = a/b", "z = a/b", OpType.Div),
            ("inv", "z = 1/b", "z = 1/b", OpType.Inv),
            ("pow", "b = a**d", "b = a^d", OpType.Pow),
            ("sqr", "b = a**2", "b = a^2", OpType.Sqr),
            ("id1", "b = 7", "b = 7", OpType.Id),
            ("id2", "b = a", "b = a", OpType.Id),
        ]
    )
    def test_str(self, name, module, result, op_type):
        code = parse(module, mode="exec")
        op = CodeOp(code)
        self.assertEqual(str(op), result)
        self.assertEqual(op.operator, op_type)

    @parameterized.expand(
        [
            ("add", "x = a+b", {"a": Mod(5, 21), "b": Mod(7, 21)}, Mod(12, 21)),
            ("sub", "x = a-b", {"a": Mod(7, 21), "b": Mod(5, 21)}, Mod(2, 21)),
        ]
    )
    def test_call(self, name, module, locals, result):
        code = parse(module, mode="exec")
        op = CodeOp(code)
        res = op(**locals)
        self.assertEqual(res, result)


class OpResultTests(TestCase):
    def test_str(self):
        for op in (OpType.Add, OpType.Sub, OpType.Mult, OpType.Div):
            res = OpResult("X1", Mod(0, 5), op, Mod(2, 5), Mod(3, 5))
            self.assertEqual(str(res), "X1")
            self.assertEqual(repr(res), f"X1 = 2{op.op_str}3")
