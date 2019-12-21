from ast import parse
from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.mod import Mod
from pyecsca.ec.op import CodeOp


class OpTests(TestCase):

    @parameterized.expand([
        ("add", "x = a+b", "x = a+b"),
        ("sub", "x = a-b", "x = a-b"),
        ("mul", "y = a*b", "y = a*b"),
        ("div", "z = a/b", "z = a/b"),
        ("pow", "b = a**d", "b = a^d")
    ])
    def test_str(self, name, module, result):
        code = parse(module, mode="exec")
        op = CodeOp(code)
        self.assertEqual(str(op), result)

    @parameterized.expand([
        ("add", "x = a+b", {"a": Mod(5, 21), "b": Mod(7, 21)}, Mod(12, 21)),
        ("sub", "x = a-b", {"a": Mod(7, 21), "b": Mod(5, 21)}, Mod(2, 21))
    ])
    def test_call(self, name, module, locals, result):
        code = parse(module, mode="exec")
        op = CodeOp(code)
        res = op(**locals)
        self.assertEqual(res, result)
