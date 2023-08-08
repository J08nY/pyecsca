import pytest

from pyecsca.ec.context import (
    local,
    DefaultContext,
    Tree,
    PathContext
)
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mod import RandomModAction
from pyecsca.ec.mult import LTRMultiplier, ScalarMultiplicationAction


def test_walk_by_key():
    tree = Tree()
    tree["a"] = Tree()
    tree["a"]["1"] = Tree()
    tree["a"]["2"] = Tree()
    assert "a" in tree
    assert isinstance(tree.get_by_key([]), Tree)
    assert isinstance(tree.get_by_key(["a"]), Tree)
    assert isinstance(tree.get_by_key(["a", "1"]), Tree)


def test_walk_by_index():
    tree = Tree()
    a = Tree()
    tree["a"] = a
    d = Tree()
    b = Tree()
    tree["a"]["d"] = d
    tree["a"]["b"] = b
    assert "a" in tree
    with pytest.raises(ValueError):
        tree.get_by_index([])

    assert tree.get_by_index([0]) == ("a", a)
    assert tree.get_by_index([0, 0]) == ("d", d)


def test_repr():
    tree = Tree()
    tree["a"] = Tree()
    tree["a"]["1"] = Tree()
    tree["a"]["2"] = Tree()
    txt = tree.repr()
    assert txt.count("\t") == 2
    assert txt.count("\n") == 3


@pytest.fixture()
def mult(secp128r1):
    base = secp128r1.generator
    coords = secp128r1.curve.coordinate_model
    mult = LTRMultiplier(
        coords.formulas["add-1998-cmo"],
        coords.formulas["dbl-1998-cmo"],
        coords.formulas["z"],
        always=True,
    )
    mult.init(secp128r1, base)
    return mult


def test_null(mult):
    with local() as ctx:
        mult.multiply(59)
    assert ctx is None


def test_default(mult):
    with local(DefaultContext()) as ctx:
        result = mult.multiply(59)
    assert len(ctx.actions) == 1
    action = next(iter(ctx.actions.keys()))
    assert isinstance(action, ScalarMultiplicationAction)
    assert result == action.result


def test_default_no_enter():
    with local(DefaultContext()) as default, pytest.raises(ValueError):
        default.exit_action(RandomModAction(7))


def test_path(mult, secp128r1):
    with local(PathContext([0, 1])) as ctx:
        key_generator = KeyGeneration(mult, secp128r1, True)
        key_generator.generate()
    assert isinstance(ctx.value, ScalarMultiplicationAction)
    with local(PathContext([0, 1, 7])):
        key_generator = KeyGeneration(mult, secp128r1, True)
        key_generator.generate()


def test_str(mult):
    with local(DefaultContext()) as default:
        mult.multiply(59)
    assert str(default) is not None
    assert str(default.actions) is not None
    with local(None):
        mult.multiply(59)
