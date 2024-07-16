from public import public
from pyecsca.ec.error import (
    raise_non_invertible,
    raise_non_residue,
)

from pyecsca.ec.mod.base import Mod, extgcd, miller_rabin, jacobi


@public
class RawMod(Mod):
    """An element x of ℤₙ (implemented using Python integers)."""

    x: int
    n: int
    __slots__ = ("x", "n")

    def __init__(self, x: int, n: int):
        self.x = x % n
        self.n = n

    def bit_length(self):
        return self.x.bit_length()

    def inverse(self) -> "RawMod":
        if self.x == 0:
            raise_non_invertible()
        x, _, d = extgcd(self.x, self.n)
        if d != 1:
            raise_non_invertible()
        return RawMod(x, self.n)

    def is_residue(self):
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return True
        if self.n == 2:
            return self.x in (0, 1)
        legendre_symbol = jacobi(self.x, self.n)
        return legendre_symbol == 1

    def sqrt(self) -> "RawMod":
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return RawMod(0, self.n)
        if not self.is_residue():
            raise_non_residue()
        if self.n % 4 == 3:
            return self ** int((self.n + 1) // 4)
        q = self.n - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1

        z = 2
        while RawMod(z, self.n).is_residue():
            z += 1

        m = s
        c = RawMod(z, self.n) ** q
        t = self**q
        r_exp = (q + 1) // 2
        r = self**r_exp

        while t != 1:
            i = 1
            while not (t ** (2**i)) == 1:
                i += 1
            two_exp = m - (i + 1)
            b = c ** int(RawMod(2, self.n) ** two_exp)
            m = int(RawMod(i, self.n))
            c = b**2
            t *= c
            r *= b
        return r

    def __bytes__(self):
        return self.x.to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

    def __int__(self):
        return self.x

    def __eq__(self, other):
        if type(other) is int:
            return self.x == (other % self.n)
        if type(other) is not RawMod:
            return False
        return self.x == other.x and self.n == other.n

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self.x)

    def __hash__(self):
        return hash(("RawMod", self.x, self.n))

    def __pow__(self, n, _=None) -> "RawMod":
        if type(n) is not int:
            raise TypeError
        if n == 0:
            return RawMod(1, self.n)
        if n < 0:
            return self.inverse() ** (-n)
        if n == 1:
            return RawMod(self.x, self.n)

        return RawMod(pow(self.x, n, self.n), self.n)


from pyecsca.ec.mod.base import _mod_classes  # noqa

_mod_classes["python"] = RawMod
