from pyecsca.ec.scalar import convert_base, sliding_window_ltr, sliding_window_rtl, wnaf, naf


def test_convert():
    assert convert_base(5, 2) == [1, 0, 1]
    assert convert_base(10, 5) == [0, 2]


def test_sliding_window():
    assert sliding_window_ltr(181, 3) == [5, 0, 0, 5, 0, 1]
    assert sliding_window_rtl(181, 3) == [1, 0, 0, 3, 0, 0, 0, 5]


def test_nafs():
    i = 0b1100110101001101011011
    assert naf(i) == wnaf(i, 2)
