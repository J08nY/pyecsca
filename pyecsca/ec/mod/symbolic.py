from functools import wraps

from public import public
from sympy import Expr

from pyecsca.ec.mod.base import Mod


def _check(func):
    @wraps(func)
    def method(self, other):
        if self.__class__ is not type(other):
            other = self.__class__(other, self.n)
        elif self.n != other.n:
            raise ValueError
        return func(self, other)

    return method


@public
class SymbolicMod(Mod):
    """A symbolic element x of ℤₙ (implemented using sympy)."""

    x: Expr
    n: int
    __slots__ = ("x", "n")

    def __init__(self, x: Expr, n: int):
        self.x = x
        self.n = n

    @_check
    def __add__(self, other) -> "SymbolicMod":
        return self.__class__((self.x + other.x), self.n)

    @_check
    def __radd__(self, other) -> "SymbolicMod":
        return self + other

    @_check
    def __sub__(self, other) -> "SymbolicMod":
        return self.__class__((self.x - other.x), self.n)

    @_check
    def __rsub__(self, other) -> "SymbolicMod":
        return -self + other

    def __neg__(self) -> "SymbolicMod":
        return self.__class__(-self.x, self.n)

    def bit_length(self):
        raise NotImplementedError

    def inverse(self) -> "SymbolicMod":
        return self.__class__(self.x ** (-1), self.n)

    def sqrt(self) -> "SymbolicMod":
        raise NotImplementedError

    def is_residue(self):
        raise NotImplementedError

    def __invert__(self) -> "SymbolicMod":
        return self.inverse()

    @_check
    def __mul__(self, other) -> "SymbolicMod":
        return self.__class__(self.x * other.x, self.n)

    @_check
    def __rmul__(self, other) -> "SymbolicMod":
        return self * other

    @_check
    def __truediv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_check
    def __rtruediv__(self, other) -> "SymbolicMod":
        return ~self * other

    @_check
    def __floordiv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_check
    def __rfloordiv__(self, other) -> "SymbolicMod":
        return ~self * other

    def __bytes__(self):
        return int(self.x).to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

    def __int__(self):
        return int(self.x)

    def __eq__(self, other):
        if type(other) is int:
            return self.x == other % self.n
        if type(other) is not SymbolicMod:
            return False
        return self.x == other.x and self.n == other.n

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self.x)

    def __hash__(self):
        return hash(("SymbolicMod", self.x, self.n))

    def __pow__(self, n, _=None) -> "SymbolicMod":
        return self.__class__(pow(self.x, n), self.n)


from pyecsca.ec.mod.base import _mod_classes  # noqa

_mod_classes["symbolic"] = SymbolicMod
