from functools import lru_cache, wraps, partial
from typing import Union

from public import public

from pyecsca.ec.mod.base import Mod, cube_root_inner, square_root_inner
from pyecsca.ec.error import (
    raise_non_invertible,
    raise_non_residue,
)

has_gmp = False
try:
    import gmpy2

    has_gmp = True
except ImportError:
    gmpy2 = None


def _check(func):
    @wraps(func)
    def method(self, other):
        if self.__class__ is not type(other):
            other = self.__class__(other, self.n)
        elif self.n != other.n:
            raise ValueError
        return func(self, other)

    return method


if has_gmp:

    @lru_cache
    def _gmpy_is_prime(x) -> bool:
        return gmpy2.is_prime(x)

    @public
    class GMPMod(Mod["GMPMod"]):
        """An element x of ℤₙ. Implemented by GMP."""

        x: gmpy2.mpz
        n: gmpy2.mpz
        __slots__ = ("x", "n")

        def __init__(
            self,
            x: Union[int, gmpy2.mpz],
            n: Union[int, gmpy2.mpz],
            ensure: bool = True,
        ):
            if ensure:
                self.n = gmpy2.mpz(n)
                self.x = gmpy2.mpz(x % self.n)
            else:
                self.n = n
                self.x = x

        def bit_length(self):
            return self.x.bit_length()

        def inverse(self) -> "GMPMod":
            if self.x == 0:
                raise_non_invertible()
            if self.x == 1:
                return GMPMod(gmpy2.mpz(1), self.n, ensure=False)
            try:
                res = gmpy2.invert(self.x, self.n)
            except ZeroDivisionError:
                raise_non_invertible()
                res = gmpy2.mpz(0)
            return GMPMod(res, self.n, ensure=False)

        def is_residue(self) -> bool:
            if not _gmpy_is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return True
            if self.n == 2:
                return self.x in (0, 1)
            return gmpy2.legendre(self.x, self.n) == 1

        def sqrt(self) -> "GMPMod":
            if not _gmpy_is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return GMPMod(gmpy2.mpz(0), self.n, ensure=False)
            if not self.is_residue():
                raise_non_residue()
            return square_root_inner(self, gmpy2.mpz, lambda x: GMPMod(x, self.n, ensure=False))

        def is_cubic_residue(self) -> bool:
            if not _gmpy_is_prime(self.n):
                raise NotImplementedError
            if self.x in (0, 1):
                return True
            if self.n % 3 == 2:
                return True
            pm1 = self.n - 1
            r = self ** (pm1 // 3)
            return r == 1

        def cube_root(self) -> "GMPMod":
            if not _gmpy_is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return GMPMod(gmpy2.mpz(0), self.n, ensure=False)
            if self.x == 1:
                return GMPMod(gmpy2.mpz(1), self.n,  ensure=False)
            if not self.is_cubic_residue():
                raise_non_residue()
            return cube_root_inner(self, gmpy2.mpz, lambda x: GMPMod(x, self.n, ensure=False))

        @_check
        def __add__(self, other) -> "GMPMod":
            return GMPMod((self.x + other.x) % self.n, self.n, ensure=False)

        @_check
        def __sub__(self, other) -> "GMPMod":
            return GMPMod((self.x - other.x) % self.n, self.n, ensure=False)

        def __neg__(self) -> "GMPMod":
            return GMPMod(self.n - self.x, self.n, ensure=False)

        @_check
        def __mul__(self, other) -> "GMPMod":
            return GMPMod((self.x * other.x) % self.n, self.n, ensure=False)

        def __bytes__(self):
            return int(self.x).to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

        def __int__(self):
            return int(self.x)

        def __eq__(self, other):
            if type(other) is int:
                return self.x == (gmpy2.mpz(other) % self.n)
            if type(other) is not GMPMod:
                return False
            return self.x == other.x and self.n == other.n

        def __ne__(self, other):
            return not self == other

        def __repr__(self):
            return str(int(self.x))

        def __hash__(self):
            return hash(("GMPMod", self.x, self.n))

        def __pow__(self, n, _=None) -> "GMPMod":
            if type(n) not in (int, gmpy2.mpz):
                raise TypeError
            if n == 0:
                return GMPMod(gmpy2.mpz(1), self.n, ensure=False)
            if n < 0:
                return self.inverse() ** (-n)
            if n == 1:
                return GMPMod(self.x, self.n, ensure=False)
            return GMPMod(
                gmpy2.powmod(self.x, gmpy2.mpz(n), self.n), self.n, ensure=False
            )

    from pyecsca.ec.mod.base import _mod_classes

    _mod_classes["gmp"] = GMPMod
