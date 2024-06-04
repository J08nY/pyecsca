import pytest

from pyecsca.ec.context import (
    local,
    DefaultContext,
    Node,
    PathContext, Action
)
from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mod import RandomModAction
from pyecsca.ec.mult import LTRMultiplier, ScalarMultiplicationAction


def test_walk_by_key():
    tree = Node(Action())
    a_a = Action()
    a = Node(a_a, parent=tree)
    one_a = Action()
    one = Node(one_a, parent=a)
    other_a = Action()
    other = Node(other_a, parent=a)

    assert tree.get_by_key([]) == tree
    assert tree.get_by_key([a_a]) == a
    assert tree.get_by_key(([a_a, one_a])) == one
    assert tree.get_by_key(([a_a, other_a])) == other


def test_walk_by_index():
    tree = Node(Action())
    a_a = Action()
    a = Node(a_a, parent=tree)
    one_a = Action()
    one = Node(one_a, parent=a)
    other_a = Action()
    other = Node(other_a, parent=a)

    assert tree.get_by_index([]) == tree
    assert tree.get_by_index([0]) == a
    assert tree.get_by_index([0, 0]) == one
    assert tree.get_by_index([0, 1]) == other


def test_render():
    tree = Node(Action())
    a_a = Action()
    a = Node(a_a, parent=tree)
    one_a = Action()
    Node(one_a, parent=a)
    other_a = Action()
    Node(other_a, parent=a)

    txt = tree.render()
    assert txt == """Action()
└──Action()
   ├──Action()
   └──Action()"""


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
    action = ctx.actions[0].action
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
