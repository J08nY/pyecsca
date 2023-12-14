from pyecsca.ec.scalar import (
    convert_base,
    sliding_window_ltr,
    sliding_window_rtl,
    wnaf,
    naf,
    booth,
    booth_word,
    booth_window,
)


def test_convert():
    assert convert_base(5, 2) == [1, 0, 1]
    assert convert_base(10, 5) == [0, 2]


def test_sliding_window():
    assert sliding_window_ltr(181, 3) == [5, 0, 0, 5, 0, 1]
    assert sliding_window_rtl(181, 3) == [1, 0, 0, 3, 0, 0, 0, 5]


def test_nafs():
    i = 0b1100110101001101011011
    assert naf(i) == wnaf(i, 2)


def test_booth():
    assert booth(0b101) == [-1, 1, -1, 1]
    for i in range(2**6):
        bw = booth_word(i, 5)
        # verified with BoringSSL recoding impl. (ec_GFp_nistp_recode_scalar_bits)
        if i <= 31:
            assert bw == (i + 1) // 2
        else:
            assert bw == -((64 - i) // 2)
    s = 0x12345678123456781234567812345678123456781234567812345678
    bw = booth_window(s, 5, 224)
    # verified with BoringSSL ec_GFp_nistp224_point_mul
    assert bw == [1, 4, 13, 3, -10, 15, 0, 9, 3, 9, -10, -12, -8, 2, 9, -6, 5, 13, -2, 1, -14, 7, -15, 11, 8, -16, 5, -14, -12, 11, -6, -4, 1, 4, 13, 3, -10, 15, 0, 9, 3, 9, -10, -12, -8]
