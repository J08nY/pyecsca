from unittest import TestCase

from pyecsca.ec.context import (local, DefaultContext, NullContext, getcontext,
                                setcontext, resetcontext, Tree)
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
        self.mult = LTRMultiplier(self.coords.formulas["add-1998-cmo"],
                                  self.coords.formulas["dbl-1998-cmo"], self.coords.formulas["z"])
        self.mult.init(self.secp128r1, self.base)

    def test_null(self):
        with local() as ctx:
            self.mult.multiply(59)
        self.assertIsInstance(ctx, NullContext)

    def test_default(self):
        token = setcontext(DefaultContext())
        self.addCleanup(resetcontext, token)

        with local(DefaultContext()) as ctx:
            result = self.mult.multiply(59)
        self.assertEqual(len(ctx.actions), 1)
        action = next(iter(ctx.actions.keys()))
        self.assertIsInstance(action, ScalarMultiplicationAction)
        self.assertEqual(len(getcontext().actions), 0)
        self.assertEqual(result, action.result)

    def test_default_no_enter(self):
        with local(DefaultContext()) as default:
            with self.assertRaises(ValueError):
                default.exit_action(RandomModAction(7))

    def test_str(self):
        with local(DefaultContext()) as default:
            self.mult.multiply(59)
        str(default)
        str(default.actions)
        with local(NullContext()) as null:
            self.mult.multiply(59)
        str(null)
