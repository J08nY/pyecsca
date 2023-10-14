from collections import namedtuple
import numpy as np
import pytest

from pyecsca.sca import Trace, welch_ttest, student_ttest, ks_test


@pytest.fixture()
def data():
    Data = namedtuple("Data", ["a", "b", "c", "d"])
    return Data(
        a=Trace(np.array([20, 80], dtype=np.dtype("i1"))),
        b=Trace(np.array([30, 42], dtype=np.dtype("i1"))),
        c=Trace(np.array([78, 56], dtype=np.dtype("i1"))),
        d=Trace(np.array([98, 36], dtype=np.dtype("i1"))),
    )


def test_welch_ttest(data):
    assert welch_ttest([data.a, data.b], [data.c, data.d]) is not None
    a = Trace(np.array([19.8, 20.4, 19.6, 17.8, 18.5, 18.9, 18.3, 18.9, 19.5, 22.0]))
    b = Trace(np.array([28.2, 26.6, 20.1, 23.3, 25.2, 22.1, 17.7, 27.6, 20.6, 13.7]))
    c = Trace(np.array([20.2, 21.6, 27.1, 13.3, 24.2, 20.1, 11.7, 25.6, 26.6, 21.4]))

    result = welch_ttest([a, b], [b, c], dof=True, p_value=True)
    assert result is not None


def test_students_ttest(data):
    with pytest.raises(ValueError):
        student_ttest([], [])
    assert student_ttest([data.a, data.b], [data.c, data.d]) is not None


def test_ks_test(data):
    with pytest.raises(ValueError):
        assert ks_test([], [])
    assert ks_test([data.a, data.b], [data.c, data.d]) is not None
