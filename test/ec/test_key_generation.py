import pytest

from pyecsca.ec.key_generation import KeyGeneration
from pyecsca.ec.mult import LTRMultiplier


@pytest.fixture()
def mult(secp128r1):
    add = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    dbl = secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
    return LTRMultiplier(add, dbl)


def test_basic(secp128r1, mult):
    generator = KeyGeneration(mult, secp128r1)
    priv, pub = generator.generate()
    assert priv is not None
    assert pub is not None
    assert secp128r1.curve.is_on_curve(pub)
    generator = KeyGeneration(mult, secp128r1, True)
    priv, pub = generator.generate()
    assert priv is not None
    assert pub is not None
    assert secp128r1.curve.is_on_curve(pub)
