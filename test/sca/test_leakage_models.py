from pyecsca.ec.context import local, DefaultContext
from pyecsca.ec.formula import FormulaAction, OpResult
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.op import OpType
from pyecsca.sca.attack.leakage_model import Identity, Bit, Slice, HammingWeight, HammingDistance, BitLength
import pytest


def test_identity():
    val = Mod(3, 7)
    lm = Identity()
    assert lm(val) == 3


def test_bit():
    val = Mod(3, 7)
    lm = Bit(0)
    assert lm(val) == 1
    lm = Bit(4)
    assert lm(val) == 0
    with pytest.raises(ValueError):
        Bit(-3)


def test_slice():
    val = Mod(0b11110000, 0xf00)
    lm = Slice(0, 4)
    assert lm(val) == 0
    lm = Slice(1, 5)
    assert lm(val) == 0b1000
    lm = Slice(4, 8)
    assert lm(val) == 0b1111
    with pytest.raises(ValueError):
        Slice(7, 1)


def test_hamming_weight():
    val = Mod(0b11110000, 0xf00)
    lm = HammingWeight()
    assert lm(val) == 4


def test_hamming_distance():
    a = Mod(0b11110000, 0xf00)
    b = Mod(0b00010000, 0xf00)
    lm = HammingDistance()
    assert lm(a, b) == 3


def test_bit_length():
    a = Mod(0b11110000, 0xf00)
    lm = BitLength()
    assert lm(a) == 8


@pytest.fixture()
def context(secp128r1):
    scalar = 0x123456789
    mult = LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas["add-1998-cmo"],
        secp128r1.curve.coordinate_model.formulas["dbl-1998-cmo"],
        secp128r1.curve.coordinate_model.formulas["z"],
        always=True,
        complete=False,
        short_circuit=True,
    )
    with local(DefaultContext()) as ctx:
        mult.init(secp128r1, secp128r1.generator)
        mult.multiply(scalar)
    return ctx


def test_mult_hw(context):
    lm = HammingWeight()
    trace = []

    def callback(action):
        if isinstance(action, FormulaAction):
            for intermediate in action.op_results:
                leak = lm(intermediate.value)
                trace.append(leak)

    context.actions.walk(callback)
    assert len(trace) > 0


def test_mult_hd(context):
    lm = HammingDistance()
    trace = []

    def callback(action):
        if isinstance(action, FormulaAction):
            for intermediate in action.op_results:
                if intermediate.op == OpType.Mult:
                    values = list(map(lambda v: v.value if isinstance(v, OpResult) else v, intermediate.parents))
                    leak = lm(*values)
                    trace.append(leak)

    context.actions.walk(callback)
    assert len(trace) > 0
