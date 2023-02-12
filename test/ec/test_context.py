from unittest import TestCase

from pyecsca.ec.context import (
    local,
    DefaultContext,
    Tree,
    PathContext
)
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.params import get_params
from pyecsca.ec.mod import RandomModAction
from pyecsca.ec.mult import LTRMultiplier, ScalarMultiplicationAction


class TreeTests(TestCase):
    def test_walk_by_key(self):
        tree = Tree()
        tree["a"] = Tree()
        tree["a"]["1"] = Tree()
        tree["a"]["2"] = Tree()
        self.assertIn("a", tree)
        self.assertIsInstance(tree.get_by_key([]), Tree)
        self.assertIsInstance(tree.get_by_key(["a"]), Tree)
        self.assertIsInstance(tree.get_by_key(["a", "1"]), Tree)

    def test_walk_by_index(self):
        tree = Tree()
        a = Tree()
        tree["a"] = a
        d = Tree()
        b = Tree()
        tree["a"]["d"] = d
        tree["a"]["b"] = b
        self.assertIn("a", tree)
        with self.assertRaises(ValueError):
            tree.get_by_index([])

        self.assertEqual(tree.get_by_index([0]), ("a", a))
        self.assertEqual(tree.get_by_index([0, 0]), ("d", d))

    def test_repr(self):
        tree = Tree()
        tree["a"] = Tree()
        tree["a"]["1"] = Tree()
        tree["a"]["2"] = Tree()
        txt = tree.repr()
        self.assertEqual(txt.count("\t"), 2)
        self.assertEqual(txt.count("\n"), 3)


class ContextTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.mult = LTRMultiplier(
            self.coords.formulas["add-1998-cmo"],
            self.coords.formulas["dbl-1998-cmo"],
            self.coords.formulas["z"],
            always=True,
        )
        self.mult.init(self.secp128r1, self.base)

    def test_null(self):
        with local() as ctx:
            self.mult.multiply(59)
        self.assertIs(ctx, None)

    def test_default(self):
        with local(DefaultContext()) as ctx:
            result = self.mult.multiply(59)
        self.assertEqual(len(ctx.actions), 1)
        action = next(iter(ctx.actions.keys()))
        self.assertIsInstance(action, ScalarMultiplicationAction)
        self.assertEqual(result, action.result)

    def test_default_no_enter(self):
        with local(DefaultContext()) as default, self.assertRaises(ValueError):
            default.exit_action(RandomModAction(7))

    def test_path(self):
        with local(PathContext([0, 1])) as ctx:
            key_generator = KeyGeneration(self.mult, self.secp128r1, True)
            key_generator.generate()
        self.assertIsInstance(ctx.value, ScalarMultiplicationAction)
        with local(PathContext([0, 1, 7])) as ctx:
            key_generator = KeyGeneration(self.mult, self.secp128r1, True)
            key_generator.generate()

    def test_str(self):
        with local(DefaultContext()) as default:
            self.mult.multiply(59)
        str(default)
        str(default.actions)
        with local(None):
            self.mult.multiply(59)
