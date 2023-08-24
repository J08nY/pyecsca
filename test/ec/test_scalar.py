from pyecsca.ec.scalar import convert, wnaf, naf


def test_convert():
    assert convert(5, 2) == [1, 0, 1]
    assert convert(10, 5) == [0, 2]


def test_nafs():
    i = 0b1100110101001101011011
    assert naf(i) == wnaf(i, 2)
