from pyecsca.ec.params import get_params
from pyecsca.ec.transformations import M2SW, M2TE, TE2M, SW2M, SW2TE


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


def test_twistededwards():
    ed25519 = get_params("other", "Ed25519", "affine")
    m = TE2M(ed25519)
    assert m is not None
    assert m.curve.is_on_curve(m.generator)
    assert m.curve.is_neutral(m.curve.neutral)


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
