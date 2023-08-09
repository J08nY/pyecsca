from pyecsca.sca.re.zvp import unroll_formula


def test_unroll(secp128r1):
    add = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    dbl = secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
    neg = secp128r1.curve.coordinate_model.formulas["neg"]
    results = unroll_formula(add, 11)
    assert results is not None
    results = unroll_formula(dbl, 11)
    assert results is not None
    results = unroll_formula(neg, 11)
    assert results is not None
