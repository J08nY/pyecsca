import pytest

from pyecsca.ec.params import get_params
from pyecsca.ec.transformations import M2SW, M2TE, M2E, TE2M, TE2E, TE2SW, SW2M, SW2TE, SW2E


def test_montgomery():
    curve25519 = get_params("other", "Curve25519", "affine")
    sw = M2SW(curve25519)
    assert sw is not None
    assert sw.curve.is_on_curve(sw.generator)
    assert sw.curve.is_neutral(sw.curve.neutral)
    te = M2TE(curve25519)
    assert te is not None
    assert te.curve.is_on_curve(te.generator)
    assert te.curve.is_neutral(te.curve.neutral)
    e = M2E(curve25519)
    assert e is not None
    assert e.curve.is_on_curve(e.generator)
    assert e.curve.is_neutral(e.curve.neutral)


def test_twistededwards():
    ed25519 = get_params("other", "Ed25519", "affine")
    m = TE2M(ed25519)
    assert m is not None
    assert m.curve.is_on_curve(m.generator)
    assert m.curve.is_neutral(m.curve.neutral)
    e = TE2E(ed25519)
    assert e is not None
    assert e.curve.is_on_curve(e.generator)
    assert e.curve.is_neutral(e.curve.neutral)
    sw = TE2SW(ed25519)
    assert sw is not None
    assert sw.curve.is_on_curve(sw.generator)
    assert sw.curve.is_neutral(sw.curve.neutral)


def test_shortweierstrass():
    secp128r2 = get_params("secg", "secp128r2", "affine")
    m = SW2M(secp128r2)
    assert m is not None
    assert m.curve.is_on_curve(m.generator)
    assert m.curve.is_neutral(m.curve.neutral)
    te = SW2TE(secp128r2)
    assert te is not None
    assert te.curve.is_on_curve(te.generator)
    assert te.curve.is_neutral(te.curve.neutral)
    with pytest.raises(ValueError):
        SW2E(secp128r2)
