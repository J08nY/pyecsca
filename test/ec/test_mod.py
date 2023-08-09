import warnings

import pytest
from sympy import FF, symbols

from pyecsca.ec.mod import (
    Mod,
    gcd,
    extgcd,
    Undefined,
    miller_rabin,
    has_gmp,
    RawMod,
    SymbolicMod,
    jacobi,
)
from pyecsca.ec.error import (
    NonInvertibleError,
    NonResidueError,
    NonInvertibleWarning,
    NonResidueWarning,
)
from pyecsca.misc.cfg import getconfig, TemporaryConfig


def test_gcd():
    assert gcd(15, 20) == 5
    assert extgcd(15, 0) == (1, 0, 15)
    assert extgcd(15, 20) == (-1, 1, 5)


def test_jacobi():
    assert jacobi(5, 1153486465415345646578465454655646543248656451) == 1
    assert jacobi(564786456646845, 46874698564153465453246546545456849797895547657) == -1
    assert jacobi(564786456646845, 46874698564153465453246546545456849797895) == 0


def test_miller_rabin():
    assert miller_rabin(2)
    assert miller_rabin(3)
    assert miller_rabin(5)
    assert not miller_rabin(8)
    assert miller_rabin(0xE807561107CCF8FA82AF74FD492543A918CA2E9C13750233A9)
    assert not miller_rabin(0x6F6889DEB08DA211927370810F026EB4C17B17755F72EA005)


def test_inverse():
    p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
    assert Mod(
        0x702BDAFD3C1C837B23A1CB196ED7F9FADB333C5CFE4A462BE32ADCD67BFB6AC1, p
    ).inverse() == Mod(0x1CB2E5274BBA085C4CA88EEDE75AE77949E7A410C80368376E97AB22EB590F9D, p)
    with pytest.raises(NonInvertibleError):
        Mod(0, p).inverse()
    with pytest.raises(NonInvertibleError):
        Mod(5, 10).inverse()
    getconfig().ec.no_inverse_action = "warning"
    with warnings.catch_warnings(record=True) as w:
        Mod(0, p).inverse()
        assert issubclass(w[0].category, NonInvertibleWarning)
    with warnings.catch_warnings(record=True) as w:
        Mod(5, 10).inverse()
        assert issubclass(w[0].category, NonInvertibleWarning)
    getconfig().ec.no_inverse_action = "ignore"
    Mod(0, p).inverse()
    Mod(5, 10).inverse()
    getconfig().ec.no_inverse_action = "error"


def test_is_residue():
    assert Mod(4, 11).is_residue()
    assert not Mod(11, 31).is_residue()
    assert Mod(0, 7).is_residue()
    assert Mod(1, 2).is_residue()


def test_sqrt():
    p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
    assert Mod(
        0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC, p
    ).sqrt() in (
               0x9ADD512515B70D9EC471151C1DEC46625CD18B37BDE7CA7FB2C8B31D7033599D,
               0x6522AED9EA48F2623B8EEAE3E213B99DA32E74C9421835804D374CE28FCCA662,
           )
    with pytest.raises(NonResidueError):
        Mod(
            0x702BDAFD3C1C837B23A1CB196ED7F9FADB333C5CFE4A462BE32ADCD67BFB6AC1, p
        ).sqrt()
    getconfig().ec.non_residue_action = "warning"
    with warnings.catch_warnings(record=True) as w:
        Mod(
            0x702BDAFD3C1C837B23A1CB196ED7F9FADB333C5CFE4A462BE32ADCD67BFB6AC1, p
        ).sqrt()
        assert issubclass(w[0].category, NonResidueWarning)
    getconfig().ec.non_residue_action = "ignore"
    Mod(
        0x702BDAFD3C1C837B23A1CB196ED7F9FADB333C5CFE4A462BE32ADCD67BFB6AC1, p
    ).sqrt()
    with TemporaryConfig() as cfg:
        cfg.ec.non_residue_action = "warning"
        with warnings.catch_warnings(record=True) as w:
            Mod(
                0x702BDAFD3C1C837B23A1CB196ED7F9FADB333C5CFE4A462BE32ADCD67BFB6AC1,
                p,
            ).sqrt()
            assert issubclass(w[0].category, NonResidueWarning)
    assert Mod(0, p).sqrt() == Mod(0, p)
    q = 0x75D44FEE9A71841AE8403C0C251FBAD
    assert Mod(0x591E0DB18CF1BD81A11B2985A821EB3, q).sqrt() in \
           (0x113B41A1A2B73F636E73BE3F9A3716E, 0x64990E4CF7BA44B779CC7DCC8AE8A3F)
    getconfig().ec.non_residue_action = "error"


def test_eq():
    assert Mod(1, 7) == 1
    assert Mod(1, 7) != "1"
    assert Mod(1, 7) == Mod(1, 7)
    assert Mod(1, 7) != Mod(5, 7)
    assert Mod(1, 7) != Mod(1, 5)


def test_pow():
    a = Mod(5, 7)
    assert a ** (-1) == a.inverse()
    assert a ** 0 == Mod(1, 7)
    assert a ** (-2) == a.inverse() ** 2


def test_wrong_mod():
    a = Mod(5, 7)
    b = Mod(4, 11)
    with pytest.raises(ValueError):
        a + b


def test_wrong_pow():
    a = Mod(5, 7)
    c = Mod(4, 11)
    with pytest.raises(TypeError):
        a ** c


def test_other():
    a = Mod(5, 7)
    b = Mod(3, 7)
    assert int(-a) == 2
    assert str(a) == "5"
    assert 6 - a == Mod(1, 7)
    assert a != b
    assert a / b == Mod(4, 7)
    assert a // b == Mod(4, 7)
    assert 5 / b == Mod(4, 7)
    assert 5 // b == Mod(4, 7)
    assert a / 3 == Mod(4, 7)
    assert a // 3 == Mod(4, 7)
    assert divmod(a, b) == (Mod(1, 7), Mod(2, 7))
    assert a + b == Mod(1, 7)
    assert 5 + b == Mod(1, 7)
    assert a + 3 == Mod(1, 7)
    assert a != 6
    assert hash(a) is not None


def test_undefined():
    u = Undefined()
    for k, meth in u.__class__.__dict__.items():
        if k in (
                "__module__",
                "__new__",
                "__init__",
                "__doc__",
                "__hash__",
                "__abstractmethods__",
                "_abc_impl",
                "__slots__",
                "x",
                "n"
        ):
            continue
        args = [5 for _ in range(meth.__code__.co_argcount - 1)]
        if k == "__repr__":
            assert meth(u) == "Undefined"
        elif k in ("__eq__", "__ne__"):
            assert not meth(u, *args)
        else:
            try:
                res = meth(u, *args)
                assert res == NotImplemented
            except NotImplementedError:
                pass


def test_implementation():
    if not has_gmp:
        pytest.skip("Only makes sense if more Mod implementations are available.")
    with TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = "python"
        assert isinstance(Mod(5, 7), RawMod)


def test_symbolic():
    x = symbols("x")
    p = 13
    k = FF(p)
    sx = SymbolicMod(x, p)
    a = k(3)
    b = k(5)
    r = sx * a + b
    assert isinstance(r, SymbolicMod)
    assert r.n == p
    sa = SymbolicMod(a, p)
    sb = SymbolicMod(b, p)
    assert sa == 3
    assert sa.inverse() == SymbolicMod(k(9), p)
    assert 1 / sa == SymbolicMod(k(9), p)
    assert sa + sb == 8
    assert 1 + sa == 4
    assert sa - 1 == 2
    assert 1 - sa == 11
    assert sa + 1 == 4
    assert -sa == 10
    assert sa / 2 == 8
    assert 2 / sa == 5
    assert sa // 2 == 8
    assert 2 // sa == 5
    assert int(sa) == 3
    assert sa != sb
    assert hash(sa) is not None
