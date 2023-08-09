import numpy as np

from pyecsca.sca import Trace, match_pattern, match_part, pad


def test_simple_match(plot):
    pattern = Trace(
        np.array([1, 15, 12, -10, 0, 13, 17, -1, 0], dtype=np.dtype("i1")), None
    )
    base = Trace(
        np.array(
            [0, 1, 3, 1, 2, -2, -3, 1, 15, 12, -10, 0, 13, 17, -1, 0, 3, 1],
            dtype=np.dtype("i1"),
        ),
        None,
    )
    filtered = match_part(base, 7, 9)
    assert filtered == [7]
    plot(base=base, pattern=pad(pattern, (filtered[0], 0)))


def test_multiple_match(plot):
    pattern = Trace(
        np.array([1, 15, 12, -10, 0, 13, 17, -1, 0], dtype=np.dtype("i1")), None
    )
    base = Trace(
        np.array(
            [
                0,
                1,
                3,
                1,
                2,
                -2,
                -3,
                1,
                18,
                10,
                -5,
                0,
                13,
                17,
                -1,
                0,
                3,
                1,
                2,
                5,
                13,
                8,
                -8,
                1,
                11,
                15,
                0,
                1,
                5,
                2,
                4,
            ],
            dtype=np.dtype("i1"),
        ),
        None,
    )
    filtered = match_pattern(base, pattern, 0.9)
    assert filtered == [7, 19]
    plot(
        base=base,
        pattern1=pad(pattern, (filtered[0], 0)),
        pattern2=pad(pattern, (filtered[1], 0)),
    )
