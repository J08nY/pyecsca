from pyecsca.ec.naf import naf, wnaf


def test_nafs():
    i = 0b1100110101001101011011
    assert naf(i) == wnaf(i, 2)
